import os
import logging
import re
from celery import shared_task
from typing import Optional, List

# DB 헬퍼 함수 import
from db import (
    get_best_questions_by_position,
    increment_question_usage,
    engine
)
from sqlmodel import Session, select

# EXAONE LLM import
from utils.exaone_llm import get_exaone_llm

logger = logging.getLogger("AI-Worker-QuestionGen")

class QuestionGenerator:
    """
    하이브리드 질문 생성기 (EXAONE-3.5-7.8B-Instruct 사용)
    전략: DB 재활용 (40%) + Few-Shot LLM 생성 (60%)

    Attributes:
        _instance (QuestionGenerator): 싱글톤 인스턴스
        _initialized (bool): 초기화 여부
        llm (LLM): EXAONE LLM 인스턴스

    생성자: ejm
    생성일자: 2026-02-04
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

        logger.info("Initializing Question Generator with EXAONE model")
        self.llm = get_exaone_llm()
        self._initialized = True

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        """
        하이브리드 질문 생성 로직 (이력서 및 회사 정보 기반)
        1. DB에서 검증된 질문 일부 재활용 (Reuse)
        2. 이력서 + 회사 정보로 컨텍스트 구성
        3. 재활용된 질문을 예시(Few-Shot)로 삼아 나머지 질문 생성 (Create)

        Args:
            position: 지원 직무
            interview_id: 면접 ID (이력서/회사 정보 조회용)
            count: 생성할 총 질문 수
            reuse_ratio: 재활용 비율 (0.0 ~ 1.0)

        Returns:
            List[str]: 생성된 질문 리스트

        Raises:
            ValueError: 재활용 비율이 유효하지 않을 경우

        생성자: ejm
        생성일자: 2026-02-04
        """
        from tools import ResumeTool, CompanyTool

        resume_summary = ""
        if interview_id:
            resume_info = ResumeTool.get_resume_by_interview(interview_id)
            if resume_info.get("has_resume"):
                context_parts.append(ResumeTool.format_for_llm(resume_info))
                logger.info(f"이력서 정보 로드 완료: {resume_info.get('summary', '')[:50]}...")

            # 회사 정보
            company_info = CompanyTool.get_company_by_interview(interview_id)
            if company_info.get("has_company"):
                context_parts.append(CompanyTool.format_for_llm(company_info))
                logger.info(f"회사 정보 로드 완료: {company_info.get('name', '')}")

        context = "\n\n".join(context_parts) if context_parts else ""

        # 2. DB에서 기존 질문 재활용 (Reuse)
        if reuse_count > 0:
            reused = self._reuse_questions_from_db(position, reuse_count)
            questions.extend(reused)
            logger.info(f"✅ DB에서 {len(reused)}개 질문 재활용")

        # 3. EXAONE LLM으로 새 질문 생성 (Create with Context)
        if generate_count > 0:
            generated = self.llm.generate_questions(
                position=position,
                context=context,
                examples=questions,  # Few-shot 예시로 재활용된 질문 사용
                count=generate_count
            )
            questions.extend(generated)
            logger.info(f"✅ EXAONE으로 {len(generated)}개 질문 생성 (컨텍스트 포함)")

        return questions[:count]  # 정확히 count개만 반환

    def _reuse_questions_from_db(self, position: str, count: int):
        """
        DB에서 검증된 질문 가져오기

        Args:
            position (str): 지원 직무
            count (int): 가져올 질문 수

        Returns:
            List[str]: DB에서 가져온 질문 리스트

        Raises:
            Exception: DB 조회 실패

        생성자: ejm
        생성일자: 2026-02-04
        """

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
    """
    질문 생성 Task

    Args:
        position (str): 지원 직무
        interview_id (int, optional): 면접 ID. Defaults to None.
        count (int, optional): 생성할 질문 수. Defaults to 5.

    Returns:
        List[str]: 생성된 질문 리스트

    Raises:
        Exception: 질문 생성 실패

    생성자: ejm
    생성일자: 2026-02-04
    """
    try:
        generator = QuestionGenerator()
        return generator.generate_questions(position, interview_id, count)
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
