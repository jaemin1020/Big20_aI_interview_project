import os
import logging
import re
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional, List

# DB 헬퍼 함수 import
from db import (
    get_best_questions_by_position,
    increment_question_usage,
    engine
)

logger = logging.getLogger("AI-Worker-QuestionGen")

# 모델 설정
MODEL_PATH = os.getenv("EVALUATOR_MODEL_PATH", "/app/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

class QuestionGenerator:
    """
    GGUF 기반 질문 생성기 (CPU 최적화)
    전략: DB 재활용 및 이력서 기반 구체화
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

        logger.info(f"Loading Question Gen Model from: {MODEL_PATH}")

        try:
            self.llm = LlamaCpp(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_threads=6,
                n_gpu_layers=0,
                temperature=0.7,
                max_tokens=512,
                verbose=False
            )
            logger.info("✅ Question Generator Model Loaded")
        except Exception as e:
            logger.error(f"Failed to Load Question Gen Model: {e}")
            self.llm = None

        self._initialized = True

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        from tools import ResumeTool, CompanyTool

        resume_summary = ""
        if interview_id:
            resume_info = ResumeTool.get_resume_by_interview(interview_id)
            if resume_info.get("has_resume"):
                resume_summary = resume_info.get("summary", "")

        base_questions = self._reuse_questions_from_db(position, count)
        if len(base_questions) < count:
            remaining = count - len(base_questions)
            base_questions.extend(self._get_fallback_questions(position, remaining))

        if resume_summary and self.llm:
            final_questions = []
            reuse_count = int(count * reuse_ratio)
            final_questions.extend(base_questions[:reuse_count])

            targets_to_specialize = base_questions[reuse_count:count]
            for original_q in targets_to_specialize:
                spec_qs = self._specialize_question(original_q, resume_summary, count=1)
                final_questions.extend(spec_qs)

            return final_questions[:count]

        return base_questions[:count]

    def _reuse_questions_from_db(self, position: str, count: int):
        try:
            db_questions = get_best_questions_by_position(position, limit=count)
            for q in db_questions:
                try:
                    increment_question_usage(q.id)
                except:
                    pass
            return [q.content for q in db_questions]
        except Exception as e:
            logger.warning(f"DB 질문 조회 실패: {e}")
            return []

    def generate_questions_from_resume(self, resume_summary: str, count: int = 5):
        """[Task 4] DB 없이 이력서만으로 면접 질문 생성"""
        prompt = f"""다음은 지원자의 이력서 요약입니다:

{resume_summary}

위 이력서를 바탕으로 지원자의 역량을 분석할 수 있는 질문을 {count}개 생성해주세요.
단순한 경험 나열이 아닌, 기술적인 역량을 확인할 수 있는 질문이어야 합니다.

형식:
1. [질문]
2. [질문]
3. [질문]

예상 질문:"""

        try:
            response = self.llm.invoke(prompt)
            lines = response.strip().split('\n')
            questions = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    q = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- ')
                    if q:
                        questions.append(q)

            if not questions:
                return ["본인의 기술적 강점에 대해 설명해 주십시오."] * count

            return questions[:count]
        except Exception as e:
            logger.error(f"이력서 기반 질문 생성 실패: {e}")
            return ["본인의 기술적 강점에 대해 설명해 주십시오."] * count

    def generate_basic_variants(self, original_question: str, count: int = 3):
        """[Task 1] 이력서 없이 질문 하나로 유사 질문 생성 (기본 성능 테스트용)"""
        prompt = f"""다음은 원본 면접 질문입니다:
"{original_question}"

위 질문과 주제는 동일하지만 표현이나 관점을 달리한 유사 질문을 {count}개 생성해주세요.

형식:
1. [질문]
2. [질문]
3. [질문]

유사 질문:"""

        try:
            response = self.llm.invoke(prompt)
            lines = response.strip().split('\n')
            questions = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    q = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- ')
                    if q:
                        questions.append(q)

            if not questions:
                return [original_question] * count

            return questions[:count]
        except Exception as e:
            logger.error(f"기본 유사질문 생성 실패: {e}")
            return [original_question] * count

    def _specialize_question(self, original_question: str, resume_summary: str, count: int = 1):
        """이력서 기반 초기 질문 생성"""
        prompt = f"""다음은 지원자의 이력서 요약입니다:

{resume_summary}

다음은 참고할 원본 면접 질문입니다:
"{original_question}"

**중요**: 위 원본 질문의 주제와 의도를 반드시 유지하면서, 이 지원자의 이력서 내용에 맞게 구체화한 질문을 {count}개 생성해주세요.

예시:
- 원본: "자기소개를 해보세요" → 생성: "보안 엔지니어로서의 경력과 KISA 인턴 경험을 중심으로 자기소개를 해주세요"
- 원본: "프로젝트 경험은?" → 생성: "Snort를 활용한 IDS 구축 프로젝트에서 어떤 역할을 맡으셨나요?"

**반드시 원본 질문의 핵심 주제를 유지하면서** 이력서의 구체적인 내용(프로젝트명, 기술명, 경험 등)을 포함해주세요.

형식:
1. [질문]
2. [질문]
3. [질문]

예상 질문:"""

        try:
            response = self.llm.invoke(prompt)
            lines = response.strip().split('\n')
            questions = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    q = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- ')
                    if q:
                        questions.append(q)

            return questions[:count] if questions else [original_question]
        except Exception as e:
            logger.error(f"질문 구체화 실패: {e}")
            return [original_question]

    def _get_fallback_questions(self, position: str, count: int) -> List[str]:
        fallback_questions = [
            f"{position} 직무에서 가장 중요하게 생각하는 역량은 무엇인가요?",
            "최근 겪었던 가장 어려운 기술적 챌린지는 무엇이었나요?",
            f"{position} 직무를 수행하는 데 필요한 핵심 기술은 무엇이라고 생각하나요?",
            "팀 프로젝트에서 의견 충돌이 있을 때 어떻게 해결하나요?",
            "본인의 강점을 실무에서 어떻게 활용할 수 있을까요?"
        ]
        return fallback_questions[:count]

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
def generate_questions_task(position: str, interview_id: int = None, count: int = 5):
    try:
        generator = QuestionGenerator()
        return generator.generate_questions(position, interview_id, count)
    except Exception as e:
        logger.error(f"Task Error: {e}")
        return []

@shared_task(name="tasks.question_generator.generate_deep_dive")
def generate_deep_dive_task(history: str, current_answer: str):
    try:
        generator = QuestionGenerator()
        return generator.generate_deep_dive_question(history, current_answer)
    except Exception as e:
        logger.error(f"Deep-Dive Task Error: {e}")
        return "관련하여 구체적인 기술적 근거를 말씀해 주십시오."

@shared_task(name="tasks.question_generator.analyze_answer_detailed")
def analyze_answer_detailed_task(history: str, current_answer: str):
    try:
        generator = QuestionGenerator()
        return generator.generate_answer_analysis(history, current_answer)
    except Exception as e:
        logger.error(f"Answer Analysis Task Error: {e}")
        return "답변 분석을 수행할 수 없습니다."
