import logging
import os
import time
import json
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# DB Helper Functions
from db import (
    update_transcript_sentiment,
    update_question_avg_score,  # 질문 평점 업데이트
    get_interview_transcripts,
    get_user_answers
)

logger = logging.getLogger("AI-Worker-Evaluator")

# --- Schemas ---

class SingleAnswerEvaluation(BaseModel):
    # 기술적 정확성 (1-5)
    technical_score: int = Field(description="기술 점수 (1-5)")
    # 의사소통 능력 (1-5)
    communication_score: int = Field(description="소통 점수 (1-5)")
    feedback: str = Field(description="상세 평가 의견")

# --- Model Setup ---
# Solar, Mistral 등 가벼운 모델 활용
MODEL_PATH = os.getenv("EVALUATOR_MODEL_PATH", "/app/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

try:
    eval_llm = LlamaCpp(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=6,
        n_gpu_layers=0,
        temperature=0.0,
        max_tokens=1024, # 출력 길이 충분히 확보
        verbose=False
    )
    logger.info("✅ Evaluator Model Loaded")
except Exception as e:
    logger.error(f"Failed to Load Model: {e}")
    eval_llm = None

@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question_text: str, answer_text: str, rubric: dict = None, question_id: int = None):
    """
    개별 답변 평가 및 점수 반영
    """
    if not eval_llm:
        logger.error("Model unavailable")
        return {"error": "Model not loaded"}

    logger.info(f"Analyzing Transcript {transcript_id} for Question {question_id}")

    # 예외 처리: 답변이 없는 경우 LLM 호출 생략
    if not answer_text or not answer_text.strip():
        logger.warning(f"Empty answer for transcript {transcript_id}. Skipping LLM evaluation.")
        return {
            "technical_score": 0,
            "communication_score": 0,
            "feedback": "No answer provided."
        }

    start_ts = time.time()

    # 1. 평가 수행
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
당신은 IT 업계의 거품을 걷어내는 20년 차 베테랑 테크 리드입니다.

# Evaluation Strategy
1. **기술적 실체 검증**: 구체적인 연구 분야와 논리적 흐름이 명확하면 긍정적으로 평가하되, 알맹이 없는 미사여구만 가득하면 비판하십시오.
2. **조직 전략 준수**: 회사의 전략적 방향을 무시하거나 임의로 수정하려는 태도는 '전략적 오만함'으로 규정하여 최하점을 주십시오.

# Output Format (JSON Only)
{{
    "technical_score": 1-5,
    "communication_score": 1-5,
    "feedback": "[기술비평] ... [비즈니스비평] ... [태도비평] ..."
}}<|eot_id|><|start_header_id|>user<|end_header_id|>
질문: {question_text}
답변: {answer_text}

위 답변을 분석하여 JSON으로만 출력하십시오.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    try:
        raw_output = eval_llm.invoke(prompt)

        # --- [방탄 JSON 복구 및 추출 로직] ---
        processed = raw_output.strip()

        # 1. 시작 괄호 찾기
        start_idx = processed.find('{')
        if start_idx == -1:
            processed = '{' + processed
            start_idx = 0

        # 2. 종료 괄호 찾기 및 자동 복구 (잘린 응답 대응)
        end_idx = processed.rfind('}')
        if end_idx == -1 or end_idx < start_idx:
            # 닫는 괄호가 없으면 인위적으로 닫음
            if processed.count('"') % 2 != 0:
                processed += '"'
            processed += '}'
            end_idx = len(processed) - 1

        # 3. JSON 블록만 추출 및 공백 정제
        json_candidate = processed[start_idx:end_idx + 1]
        json_candidate = json_candidate.replace('\n', ' ').replace('\r', ' ')

        # 4. JSON 파싱
        import json
        try:
            result_dict = json.loads(json_candidate)
        except json.JSONDecodeError:
            # 마지막 콤마 오류 등 흔한 케이스 보정 후 재시도
            import re
            json_candidate = re.sub(r',\s*}', '}', json_candidate)
            result_dict = json.loads(json_candidate)

        # 5. 후처리: 피드백 정제
        if "feedback" in result_dict:
            fb = result_dict["feedback"]
            import re
            fb = re.sub(r'\s+', ' ', fb).strip()
            result_dict["feedback"] = fb

        tech_score = result_dict.get("technical_score", 3)
        comm_score = result_dict.get("communication_score", 3)
        feedback = result_dict.get("feedback", "")
        # (5점 만점 -> -0.5 ~ 0.5 범위로 정규화 + 보정)
        sentiment = ((tech_score + comm_score) / 10.0) - 0.5

        # 3. DB 업데이트 (Transcript)
        update_transcript_sentiment(
            transcript_id,
            sentiment_score=sentiment,
            emotion="neutral" # 감정 분석은 별도 모델 필요하나 일단 점수로 대체
        )

        # 4. 질문 평점 업데이트 (선순환 구조)
        # 이 질문에 대한 평균 답변 품질이 높다면 -> 좋은 질문일 가능성이 높음 (변별력 있음)
        # 답변 점수 (0-100)
        answer_quality = (tech_score + comm_score) * 10

        if question_id:
            update_question_avg_score(question_id, answer_quality)
            logger.info(f"Updated Question {question_id} Avg Score with {answer_quality}")

        duration = time.time() - start_ts
        logger.info(f"Evaluation Completed ({duration:.2f}s)")

        return result_dict

    except Exception as e:
        logger.error(f"Evaluation Failed: {e}")
        return {"error": str(e)}

@shared_task(name="tasks.evaluator.generate_final_report")
def generate_final_report(interview_id: int):
    """
    최종 평가 리포트 생성 (엄격한 루브릭 기반)
    A(15%), B(15%), C(20%), D(25%), E(25%) 가중치 적용
    """
    from db import (
        create_or_update_evaluation_report,
        update_interview_overall_score,
        Interview, Company, Resume, Session, engine
    )

    logger.info(f"Generating Final Report for Interview {interview_id}")

    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if not interview: return

        company = session.get(Company, interview.company_id) if interview.company_id else None
        resume = session.get(Resume, interview.resume_id) if interview.resume_id else None
        transcripts = get_interview_transcripts(interview_id)

    if not transcripts:
        logger.warning("No answers found for this interview.")
        return

    # LLM용 데이터 구성
    interview_log = "\n".join([f"{t.speaker}: {t.text}" for t in transcripts])
    company_name = company.company_name if company else "일반 기업"
    talent_model = company.ideal if company else "창의 및 도전"
    resume_summary = resume.extracted_text[:1000] if resume else "이력서 정보 없음"

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 IT 기업의 시니어 면접관이자 채용 데이터 분석 전문가입니다. 제공된 [이력서], [인재상], [면접 로그]를 바탕으로 지원자의 역량을 정밀 분석하여 최종 평가 리포트를 생성하십시오.

# Evaluation Principles (Strict)
1. **데이터 기반 평가**: 모든 점수와 의견은 반드시 면접 로그 내의 구체적인 발언에 근거해야 합니다. 추측은 배제하십시오.
2. **루브릭 가중치 적용**: A(15%), B(15%), C(20%), D(25%), E(25%) 가중치를 엄격히 준수하십시오.
3. **추가 질문 비교(Critical)**: 추가 질문에 대한 답변을 초기 답변과 대조하십시오. 논리 보완 시 가산(+), 동일 내용 반복/회피 시 감점(-) 하십시오.
4. **관찰 포인트 미충족 시 감점**: 각 영역의 'LLM 관찰 포인트' 미확인 시 자동으로 하위권 점수를 부여합니다.
5. **태도 및 비즈니스 매너 검증**: 기술적 키워드 사용 여부와 별개로, 비논리적 근거로 질문을 일축하거나 무례한 태도를 보이면 '커뮤니케이션' 및 '인성' 영역에서 즉시 감점합니다.
6. **BS Detection**: "특정 자격증보다 내 기술력이 낫다"와 같은 주관적 과장이나 타 직무/요건에 대한 비하 발언은 '논리력' 결여로 간주하여 엄격히 평가합니다.

# Evaluation Rubric & Metrics
### A. 자기 표현 & 기본 커뮤니케이션 (15%)
### B. 지원 동기 & 회사 적합성 (15%)
### C. 직무 지식 이해도 (20%)
### D. 직무 경험 & 문제 해결 (25%)
### E. 인성 & 성장 가능성 (25%)

# Output Format (JSON Only)
{{
  "overall_analysis": {{
    "summary": "전체적인 면접 성과 분석"
  }},
  "total_score": 0,
  "pass_status": "PASS/FAIL/HOLD",
  "core_summary": "지원자의 핵심 역량을 한 줄로 요약",
  "detailed_metrics": {{
    "A_communication": {{ "score": 0, "reason": "관찰 포인트, 구조적 답변 및 비즈니스 매너(공격성 여부) 근거 기록" }},
    "B_fit": {{ "score": 0, "reason": "인재상 일치 여부, 지원 동기의 진정성 및 직업 윤리(속물적 언어 여부) 기술" }},
    "C_knowledge": {{ "score": 0, "reason": "개념 이해 및 추가질문 대응 시의 논리적 방어력 분석" }},
    "D_experience": {{ "score": 0, "reason": "STAR 구조 기반 기여도 및 구체적 수치 제시 여부 분석" }},
    "E_attitude": {{ "score": 0, "reason": "성장 가능성, 겸손함, 타인 의견 수용성 분석" }}
}},
  "comparative_analysis": {{
    "follow_up_improvement": "추가 질문을 통한 답변 개선/악화 사례 상세 분석"
  }},
  "feedback": {{
    "strengths": ["강점 1", "강점 2"],
    "weaknesses": ["보완점 1", "보완점 2"],
    "company_specific_advice": "[{{Company_Name}}]의 인재상에 비추어 본 최종 제언",
    "closing_quote": "지원자의 성향을 반영한 맞춤형 동기부여 명언"
  }}
}}
<|eot_id|><|start_header_id|>user<|end_header_id|>
- [Company Name]: {company_name}
- [Company Talent Model]: {talent_model}
- [Resume Summary]: {resume_summary}
- [Full Interview Log]: {interview_log}

위 데이터를 바탕으로 냉철하고 객관적인 리포트를 생성하십시오.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    try:
        raw_output = eval_llm.invoke(prompt)
        # JSON 부분만 추출
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}') + 1
        report_data = json.loads(raw_output[start_idx:end_idx])

        # DB 저장용 데이터 추출
        total_score = report_data.get("total_score", 0)
        summary = report_data.get("core_summary", "")

        create_or_update_evaluation_report(
            interview_id,
            technical_score=report_data["detailed_metrics"]["C_knowledge"]["score"],
            communication_score=report_data["detailed_metrics"]["A_communication"]["score"],
            cultural_fit_score=report_data["detailed_metrics"]["B_fit"]["score"],
            summary_text=summary,
            details_json=report_data,
            evaluator_model="Llama-3.1-8B-Strict-Evaluator-v2"
        )

        update_interview_overall_score(interview_id, total_score)
        logger.info(f"Final Report Generated successfully with score {total_score}")

    except Exception as e:
        logger.error(f"Final Report Generation Failed: {e}")