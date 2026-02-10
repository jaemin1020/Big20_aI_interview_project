import os
import logging
from celery import shared_task
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from typing import Optional, List
import torch
import re

# DB 헬퍼 함수 import
from db import engine
from sqlmodel import Session, select

logger = logging.getLogger("AI-Worker-QuestionGen")

# 모델 설정
MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"

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
        logger.info("✅ Question Generator Initialized")

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
             fallback = self.llm._get_fallback_questions(position, count - len(questions))
             questions.extend(fallback)
             
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
    
    def _generate_new_questions(self, position: str, count: int, examples: list, context: str = ""):
        """LLM으로 새 질문 생성 (Few-Shot + Context)"""
        
        
        # Few-Shot 예시 구성 (예시가 없으면 강력한 한국어 기본 예시 제공)
        if examples:
            few_shot_examples = "\n".join([f"- {q}" for q in examples[:3]])
        else:
            few_shot_examples = """
- React의 Virtual DOM이 무엇이며, 이것이 성능에 어떤 영향을 미치는지 설명해주세요.
- 비동기 프로그래밍에서 Promise와 async/await의 차이점은 무엇인가요?
- 사용해본 상태 관리 라이브러리는 무엇이며, 그 선택 이유는 무엇인가요?
"""
        
        # 컨텍스트 추가
        context_section = f"\n\n추가 컨텍스트:\n{context}" if context else ""
        
        # 사용자 요청에 따른 프롬프트 구조
        prompt = [{'role':'system','content':
        (f"""
        당신은 한국 기업의 면접관이자 채용 전문가입니다.
        아래 정보를 바탕으로 {position} 직무에 적합한 '한국어 면접 질문'을 {count}개 생성하세요.
        {context_section}
        
        기존 질문 예시:
        {few_shot_examples}
        
        [중요 요구사항]
        1. 모든 질문은 반드시 자연스러운 한국어로 작성해야 합니다. (영어, 태국어 등 타 언어 혼용 금지)
        2. 기술적 깊이와 실무 경험을 구체적으로 물어보세요.
        3. 지원자의 이력서 내용과 연관된 질문을 포함하세요. (이력서 정보가 있는 경우)
        4. 회사의 인재상과 연결된 질문을 포함하세요. (회사 정보가 있는 경우)
        5. 각 질문은 번호 없이 한 줄씩만 작성하세요.
        6. 질문의 어조는 정중하고 전문적이어야 합니다.
        7. 강조 표시(**text**) 금지
        """)}]
        
        try:
            # Llama 3.2 모델을 위한 채팅 템플릿 적용
            prompt_str = self.tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
            
            # 질문 생성을 위해 더 긴 토큰 허용 (return_full_text=False 설정 덕분에 prompt_str은 제외됨)
            response = self.llm.invoke(prompt_str)
            
            # 응답 파싱
            
            # 1. 특수 토큰 및 시스템 메시지 제거 패턴
            system_patterns = [
                r"<\|.*?\|>",  # 특수 토큰
                r"Cutting Knowledge Date",
                r"Today Date",
                r"^system$", # 헤더 잔여물
                r"^user$",
                r"^assistant$",
                r"당신은 면접 질문 생성 전문가입니다", # 프롬프트 에코 방지
                r"요구사항:",
                r"기존 질문 예시:",
                r"질문 \d+개:"
            ]
            
            clean_lines = []
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # 시스템 메시지 패턴이 포함된 라인 건너뛰기
                if any(re.search(pat, line) for pat in system_patterns):
                    continue
                
                # 프롬프트의 지시사항 문장과 유사하면 건너뛰기 (Echo 방지 2차 필터)
                if "평가할 수 있는 질문" in line or "이력서 내용과 연관" in line or "한 줄로 작성" in line:
                    continue

                # #으로 시작하는 주석 라인 건너뛰기
                if line.startswith('#'):
                    continue
                    
                clean_lines.append(line)

            # 2. 질문 추출 및 정제
            questions = []
            for line in clean_lines:
                # 번호 제거 (예: "1. 질문" -> "질문", "- 질문" -> "질문")
                clean_q = re.sub(r'^[\d\-\.\s]+', '', line)
                
                # Markdown 강조 제거 (**text** -> text)
                clean_q = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_q)
                
                # 앞뒤 따옴표 및 공백 제거
                clean_q = clean_q.strip('"\' ')
                
                # [필터링 개선] Whitelist 방식은 너무 엄격하여 Blacklist 방식으로 변경
                # 일본어(히라가나/가타카나), 한자, 태국어 등이 포함된 경우만 제외하고 나머지는 허용
                # 기술 면접 질문에는 다양한 특수문자(@, #, &, [] 등)가 사용될 수 있음
                forbidden_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u0E00-\u0E7F]'
                if re.search(forbidden_pattern, clean_q):
                    logger.warning(f"제외된 질문(다국어 포함): {clean_q}")
                    continue
                
                # 길이가 너무 짧은 것은 질문이 아닐 확률 높음 (10자 이상)
                if len(clean_q) > 10:
                    questions.append(clean_q)
            
            # 만약 결과가 부족하면 Fallback 질문으로 채움
            if len(questions) < count:
                logger.warning(f"생성된 질문 수 부족 ({len(questions)}/{count}). Fallback으로 보충합니다.")
                fallback_needed = count - len(questions)
                fallbacks = self._get_fallback_questions(position, fallback_needed)
                questions.extend(fallbacks)
                
            logger.info(f"최종 반환 질문: {questions[:count]}")
            return questions[:count]
        except Exception as e:
            logger.error(f"LLM 질문 생성 중 에러 발생: {e}")
            # 에러 발생 시에도 빈 리스트 보단 Fallback 리턴
            return self._get_fallback_questions(position, count)
    
    def _get_fallback_questions(self, position: str, count: int) -> List[str]:
        """폴백 질문 생성"""
        fallback_questions = [
            f"{position} 직무에서 가장 중요하게 생각하는 역량은 무엇인가요?",
            "최근 겪었던 가장 어려운 기술적 챌린지는 무엇이었나요?",
            f"{position} 직무를 수행하는 데 필요한 핵심 기술은 무엇이라고 생각하나요?",
            "팀 프로젝트에서 의견 충돌이 있을 때 어떻게 해결하나요?",
            "본인의 강점을 실무에서 어떻게 활용할 수 있을까요?",
            "우리 회사에 지원한 이유를 구체적으로 말씀해주세요.",
            "5년 후 본인의 모습을 어떻게 그리고 계신가요?",
            "실패한 프로젝트 경험과 그로부터 배운 점을 공유해주세요."
        ]
        return fallback_questions[:count]

@shared_task(name="tasks.question_generator.generate_questions")
def generate_questions_task(position: str, interview_id: int = None, count: int = 5):
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

