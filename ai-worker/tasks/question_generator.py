import os
import logging
import re
from celery import shared_task
from typing import Optional, List, Dict
import re

# DB 헬퍼 함수 import
from db import engine
from sqlmodel import Session, select

# EXAONE LLM import
from utils.exaone_llm import get_exaone_llm

logger = logging.getLogger("AI-Worker-QuestionGen")

class QuestionGenerator:
    """
    RAG 기반 심층 면접 질문 생성기 (EXAONE-3.5-7.8B-Instruct 사용)
    면접 단계별 시나리오(Plan)에 따라 이력서 내용을 참조하여 질문 생성

    Attributes:
        _instance (QuestionGenerator): 싱글톤 인스턴스
        _initialized (bool): 초기화 여부
        llm (ExaoneLLM): EXAONE LLM 인스턴스
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        logger.info("Initializing RAG Question Generator")
        self.llm = get_exaone_llm()
        self._initialized = True

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5) -> List[str]:
        """
        면접 단계별 RAG 기반 질문 생성

        Args:
            position: 지원 직무
            interview_id: 면접 ID
            count: 생성할 총 질문 수
        """
        questions = []

        # 1. 이력서 ID 및 지원자 정보 조회
        resume_id = None
        candidate_name = "지원자"

        if interview_id:
            try:
                with Session(engine) as session:
                    # Circular import 방지를 위해 함수 내부 import
                    from db import Interview, Resume
                    interview = session.get(Interview, interview_id)
                    if interview and interview.resume_id:
                        resume_id = interview.resume_id
                        resume = session.get(Resume, resume_id)
                        # 이력서에서 지원자 이름 추출 시도 (헤더 정보 등)
                        if resume and resume.structured_data:
                            candidate_name = resume.structured_data.get("target_company", {}).get("name", "지원자")
                            # structured_data 구조에 따라 다를 수 있음. 안전하게 처리
                            if isinstance(resume.structured_data.get("header"), dict):
                                candidate_name = resume.structured_data["header"].get("name", "지원자")
            except Exception as e:
                logger.warning(f"이력서 정보 조회 실패: {e}")

        # 2. RAG 불가능 시 기본 생성 로직으로 Fallback
        if not resume_id:
            logger.info("Resume ID not found. Using generic generation.")
            return self.llm.generate_questions(position=position, count=count)

        # 3. 면접 시나리오 정의 (Step 8 기반)
        interview_plan = [
            {
                "stage": "1. 직무 지식 평가",
                "search_query": f"{position} 핵심 기술 스킬 도구 원리",
                "filter_category": "metric", # 자격증/스킬
                "guide": "지원자가 사용한 기술(Tool, Language)의 구체적인 설정법이나, 기술적 원리(Deep Dive)를 물어볼 것."
            },
            {
                "stage": "2. 직무 경험 평가",
                "search_query": "프로젝트 성과 달성 문제해결",
                "filter_category": "project",
                "guide": "프로젝트에서 달성한 수치적 성과(%)의 결정적 요인이 무엇인지, 구체적으로 어떤 데이터를 다뤘는지 물어볼 것."
            },
            {
                "stage": "3. 문제 해결 능력 평가",
                "search_query": "기술적 난관 극복 트러블슈팅",
                "filter_category": "project",
                "guide": "직면한 한계점이나 문제 상황을 어떻게 정의했고, 어떤 논리적 사고 과정을 통해 해결책을 도출했는지 물어볼 것."
            },
            {
                "stage": "4. 의사소통 및 협업 평가",
                "search_query": "협업 갈등 해결 커뮤니케이션",
                "filter_category": "narrative",
                "guide": "팀원과의 의견 대립 상황에서 본인의 주장을 관철시키기 위해 어떤 객관적 근거를 사용했는지 대화 과정을 물어볼 것."
            },
            {
                "stage": "5. 직무 적합성 및 성장 가능성",
                "search_query": f"{position} 트렌드 성장 계획",
                "filter_category": "narrative",
                "guide": "직무와 관련된 최신 트렌드를 어떻게 학습하고 있으며, 이를 실무에 어떻게 적용할 것인지 물어볼 것."
            }
        ]

        # 4. 시나리오 반복하며 질문 생성
        # count가 plan보다 크면 plan을 반복, 작으면 앞에서부터 자름
        generated_count = 0
        plan_idx = 0

        while generated_count < count:
            step = interview_plan[plan_idx % len(interview_plan)]
            plan_idx += 1

            # RAG 검색
            contexts = self._retrieve_context(
                resume_id=resume_id,
                query=step['search_query'],
                filter_category=step['filter_category'],
                top_k=2
            )

            # 질문 생성
            if contexts:
                q = self.llm.generate_human_like_question(
                    name=candidate_name,
                    stage=step['stage'],
                    guide=step['guide'] + f" (지원 직무: {position})",
                    context_list=contexts
                )
                if q not in questions: # 중복 방지
                    questions.append(q)
                    generated_count += 1
            else:
                # 컨텍스트 없으면 Fallback 질문 하나 추가
                logger.info(f"컨텍스트 없음: {step['stage']}")
                # 그냥 다음 단계로 넘어가거나 기본 질문 추가
                # 여기서는 스킵하고 계속 진행 (while loop)
                # 무한 루프 방지: 시도를 너무 많이 하면 중단
                if plan_idx > count * 3:
                     break

        # 부족분 채우기
        if len(questions) < count:
            logger.warning(f"생성된 질문 수 부족 ({len(questions)}/{count}). Fallback으로 보충합니다.")
            fallback_candidates = self.llm._get_fallback_questions(position, count + 5) # 충분히 가져오기

            for fq in fallback_candidates:
                if len(questions) >= count:
                    break
                if fq not in questions:
                    questions.append(fq)

        return questions[:count]

    def _retrieve_context(self, resume_id: int, query: str, filter_category: str, top_k: int = 2) -> List[Dict]:
        """내부 RAG 검색 로직"""
        try:
            from db import ResumeSectionEmbedding, ResumeSectionType
            from utils.vector_utils import get_embedding_generator

            # 카테고리 매핑
            category_map = {
                "metric": [ResumeSectionType.CERTIFICATION, ResumeSectionType.SKILL, ResumeSectionType.LANGUAGE, ResumeSectionType.EDUCATION],
                "project": [ResumeSectionType.PROJECT, ResumeSectionType.EXPERIENCE],
                "narrative": [ResumeSectionType.SELF_INTRODUCTION]
            }
            target_types = category_map.get(filter_category)

            # 임베딩
            generator = get_embedding_generator()
            query_vector = generator.encode_query(query)

            # 검색
            with Session(engine) as session:
                dist_expr = ResumeSectionEmbedding.embedding.cosine_distance(query_vector)
                stmt = select(ResumeSectionEmbedding, dist_expr.label("distance")).where(
                    ResumeSectionEmbedding.resume_id == resume_id,
                    ResumeSectionEmbedding.embedding.isnot(None)
                )
                if target_types:
                    stmt = stmt.where(ResumeSectionEmbedding.section_type.in_(target_types))

                stmt = stmt.order_by(dist_expr).limit(top_k)
                rows = session.exec(stmt).all()

                return [{"text": row[0].content, "similarity": 1 - (row[1]/2)} for row in rows]

        except Exception as e:
            logger.error(f"RAG 검색 실패: {e}")
            return []

    def generate_deep_dive_question(self, history: str, current_answer: str):
        """동적 꼬리질문(Deep-Dive) 생성 - 면접관 톤으로 생성"""
        if not self.llm: return "추가 질문을 구성할 수 없습니다."

        prompt = f"""당신은 면접관입니다. 지원자의 답변을 듣고, 더 구체적인 확인이 필요한 부분에 대해 정중하고 날카로운 꼬리질문을 하나만 던져주세요.

이전 질문: {history}
지원자 답변: {current_answer}

지점:
- 말투는 정중한 격식체(~습니까?, ~하십시오)를 사용하세요.
- 불필요한 분석이나 메타 정보 없이 '질문 문장'만 출력하세요.

질문:"""

        try:
            response = self.llm.invoke(prompt)
            # 질문만 깔끔하게 추출
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and not line.startswith('###'):
                    # "질문:" 이나 숫자 등이 포함된 경우 제거
                    clean_q = re.sub(r'^(질문|질문 내용|Q|A|1|2|3|4|5)[\.\s:]+', '', line).strip()
                    # 끝에 붙는 노이즈(날짜, 점수 등) 제거
                    clean_q = re.sub(r'\s*\|.*\|?\s*$', '', clean_q).strip()
                    if len(clean_q) > 10:
                        return clean_q

            return response.strip()

        except Exception as e:
            logger.error(f"Deep-Dive 생성 실패: {e}")
            return "방금 말씀하신 부분과 관련하여, 실무에서 어떤 방식으로 문제를 해결하셨는지 조금 더 구체적으로 말씀해 주시겠습니까?"

    def generate_answer_analysis(self, history: str, current_answer: str):
        """[Task 3] 답변 정밀 분석 - 섹션 기반 파싱 (줄바꿈 허용)"""
        if not self.llm: return "분석을 수행할 수 없습니다."

        prompt = f"""당신은 면접관입니다. 지원자의 답변을 기술적 구체성, 수치 및 성과, 논리적 정합성, 실무 적용성, 종합 평가 5가지 기준으로 평가하십시오.
각 항목에 대해 점수([점수/5])와 구체적인 이유를 작성하십시오.

질문: {history}
답변: {current_answer}

[평가 시작]
- 기술적 구체성:"""

        try:
            response = self.llm.invoke(prompt).strip()
            # 로그로 원본 확인
            logger.info(f"Raw Analysis Response:\n{response}")

            full_response = "- 기술적 구체성: " + response

            import re
            categories = ["기술적 구체성", "수치 및 성과", "논리적 정합성", "실무 적용성", "종합 평가"]

            # 1. 각 카테고리의 시작 위치 찾기
            # (?:-|\d+\.|#)? \s* 카테고리명 \s* :?
            # 위 패턴으로 각 카테고리가 텍스트 내 어디에 있는지 인덱싱
            indices = []
            for cat in categories:
                # 유연한 매칭: 앞부분 기호(-, 1., # 등) 허용, 콜론 허용
                pattern = r'(?:-|\d+\.|#)?\s*' + re.escape(cat) + r'\s*:?'
                match = re.search(pattern, full_response)
                if match:
                    indices.append((match.start(), cat))

            # 위치 순서대로 정렬
            indices.sort()

            results = []

            for i, (start_idx, cat) in enumerate(indices):
                # 현재 카테고리부터 다음 카테고리 시작 전까지가 내용
                end_idx = indices[i+1][0] if i + 1 < len(indices) else len(full_response)

                content_chunk = full_response[start_idx:end_idx]

                # 카테고리 헤더 제거 (예: "- 기술적 구체성:")
                # 첫 번째 콜론(:) 이후 내용을 가져오거나, 헤더 길이만큼 자름
                split_content = content_chunk.split(':', 1)
                if len(split_content) > 1:
                    content_body = split_content[1]
                else:
                    # 콜론이 없으면 카테고리 이름 길이만큼 넘김 (대충 처리)
                    content_body = content_chunk[len(cat):]

                # 점수 찾기
                score_pattern = r'(\d+(?:\.\d+)?)\s*/\s*5|(\d+(?:\.\d+)?)\s*/\s*10|(\d+(?:\.\d+)?)\s*점'
                score_match = re.search(score_pattern, content_body)

                score_txt = "0"
                if score_match:
                    val = 0.0
                    if score_match.group(1): val = float(score_match.group(1))
                    elif score_match.group(2): val = float(score_match.group(2)) / 2
                    elif score_match.group(3): val = float(score_match.group(3))

                    if val > 5.0: val = 5.0 # 보정
                    score_txt = str(int(val)) if val.is_integer() else str(val)

                    # 점수 부분 제거 (내용 정제용)
                    content_body = content_body.replace(score_match.group(0), '')

                # 내용 정제
                # 대괄호 잔여물 [ ] 제거
                content_body = re.sub(r'\[\s*\]', '', content_body)
                content_body = re.sub(r'\[\s*/\s*5\s*\]', '', content_body)

                # 불필요한 공백/줄바꿈 압축
                reason = " ".join(content_body.split()).strip()
                # 앞부분 기호 제거 (. , - )
                reason = re.sub(r'^[\.\,\-\s]+', '', reason)

                if reason:
                    results.append(f"- {cat}: {score_txt}/5점. {reason}")

            if len(results) >= 3:
                return "\n".join(results)

            return full_response[:300]

        except Exception as e:
            logger.error(f"답변 분석 실패: {e}")
            return "답변 분석 중 오류가 발생했습니다."

@shared_task(name="tasks.question_generator.generate_questions")
def generate_questions_task(position: str, interview_id: int = None, count: int = 1):
    """
    질문 생성 Task (TTS 포함)

    Args:
        position (str): 지원 직무
        interview_id (int, optional): 면접 ID. Defaults to None.
        count (int, optional): 생성할 질문 수. Defaults to 5.

    Returns:
        List[Dict[str, str]]: 생성된 질문 및 오디오 URL 리스트
        Example: [{"text": "질문내용", "audio_url": "/static/audio/..."}]

    Raises:
        Exception: 질문 생성 실패

    생성자: ejm
    생성일자: 2026-02-04
    """
    import uuid
    from .tts import tts_engine, load_tts_engine

    try:
        generator = QuestionGenerator()
        questions = generator.generate_questions(position, interview_id, count)

        # TTS Integration
        results = []

        # Ensure TTS engine is ready
        if tts_engine is None or tts_engine.tts is None:
            load_tts_engine()

        # Save directory inside container
        save_dir = "/app/uploads/audio"
        os.makedirs(save_dir, exist_ok=True)

        for q in questions:
            audio_url = None
            if tts_engine and tts_engine.tts:
                try:
                    filename = f"q_{uuid.uuid4().hex}.wav"
                    filepath = os.path.join(save_dir, filename)

                    if tts_engine.synthesize(q, filepath):
                        # URL path for backend (mounted as /static)
                        audio_url = f"/static/audio/{filename}"
                except Exception as ex:
                    logger.error(f"TTS failing for question '{q[:20]}...': {ex}")

            results.append({"text": q, "audio_url": audio_url})

        return results

    except Exception as e:
        logger.error(f"Task Error: {e}")
        return []

# Eager Initialization: Worker 시작 시 모델 미리 로드
try:
    logger.info("🔥 Pre-loading Question Generator with EXAONE...")
    _warmup_generator = QuestionGenerator()
    logger.info("✅ Question Generator ready for requests")
except Exception as e:
    logger.warning(f"⚠️ Failed to pre-load model (will load on first request): {e}")
