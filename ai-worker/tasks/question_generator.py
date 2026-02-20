import os
import sys
import json
import gc
import logging
import torch
from datetime import datetime
from celery import shared_task
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 초기 설정
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# 모델 경로 설정
local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
model_path = docker_path if os.path.exists(docker_path) else local_path

PROMPT_TEMPLATE = """[|system|]당신은 지원자의 역량을 정밀하게 검증하는 전문 면접관입니다.
제공된 [이력서 문맥]과 [면접 진행 상황]을 바탕으로, 지원자에게 던질 '다음 질문' 1개만 생성하십시오.

[절대 규칙]
1. 반드시 한국어로 답변하십시오.
2. 질문은 명확하고 구체적이어야 하며, 150자 이내로 작성하십시오.
3. 특수문자(JSON 기호, 역따옴표 등)를 절대 사용하지 마십시오. 오직 순수 텍스트만 출력하십시오.
4. "질문:" 이라는 수식어 없이 바로 질문 본문만 출력하십시오.
5. 이전 질문과 중복되지 않도록 하십시오.

[이력서 및 답변 문맥]
{context}

[현재 면접 단계 정보]
- 단계명: {stage_name}
- 가이드: {guide}

[|user|]위 정보를 바탕으로 면접 질문을 생성해 주세요.[|endofturn|]
[|assistant|]"""

# ==========================================
# 메인 작업: 질문 생성 태스크
# ==========================================

@shared_task(bind=True, name="tasks.question_generation.generate_next_question")
def generate_next_question_task(self, interview_id: int):
    """
    인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    """
    # 늦은 임포트로 순환 참조 방지
    from db import engine, Session, select, Interview, Transcript, Speaker, Question, save_generated_question
    from utils.exaone_llm import get_exaone_llm
    from tasks.tts import synthesize_task
    from utils.rag_utils import retrieve_context  # RAG 함수 가정
    from config.interview_logic import check_if_transition, get_next_stage_normal, get_next_stage_transition

    try:
        with Session(engine) as session:
            # 1. 인터뷰 정보 로드
            interview = session.get(Interview, interview_id)
            if not interview:
                logger.error(f"Interview {interview_id} not found.")
                return {"status": "error", "message": "Interview not found"}

            # 2. 마지막 발화 확인 및 레이스 컨디션 방지
            stmt_all = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order.desc())
            last_transcript = session.exec(stmt_all).first()

            stmt_ai = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == Speaker.AI
            ).order_by(Transcript.order.desc(), Transcript.id.desc())
            last_ai_transcript = session.exec(stmt_ai).first()

            # 중복 생성 방지 (최근 10초 내 생성 여부)
            if last_ai_transcript:
                diff = (datetime.utcnow() - last_ai_transcript.timestamp).total_seconds()
                if diff < 10:
                    logger.info(f"Skipping duplicate request (diff={diff:.1f}s)")
                    return {"status": "skipped"}

            # 3. 지원자 정보 추출 (전공, 성함 등)
            major = ""
            candidate_name = "지원자"
            if interview.resume and interview.resume.structured_data:
                sd = interview.resume.structured_data
                if isinstance(sd, str): sd = json.loads(sd)
                
                edu = sd.get("education", [])
                major = next((e.get("major", "") for e in edu if e.get("major", "").strip()), "")
                candidate_name = sd.get("header", {}).get("name", "지원자")

            # 4. 다음 단계 판별
            is_transition = check_if_transition(major, interview.position)
            get_next_stage_func = get_next_stage_transition if is_transition else get_next_stage_normal
            
            if last_ai_transcript and last_ai_transcript.question_id:
                last_q = session.get(Question, last_ai_transcript.question_id)
                last_stage_name = last_q.stage if last_q else "intro"
            else:
                last_stage_name = "intro"

            next_stage = get_next_stage_func(last_stage_name)

            if not next_stage:
                interview.status = "COMPLETED"
                session.add(interview)
                session.commit()
                return {"status": "completed"}

            # 5. 질문 내용 생성 (Template vs LLM)
            final_question_body = ""
            stage_type = next_stage.get("type", "ai")

            if stage_type == "template":
                target_role = interview.position or "해당 직무"
                template_vars = {"candidate_name": candidate_name, "target_role": target_role, "major": major}
                tpl = next_stage.get("template", "{candidate_name} 지원자님, 계속해주세요.")
                try:
                    final_question_body = tpl.format(**template_vars)
                except KeyError:
                    final_question_body = tpl
            else:
                # RAG 문맥 확보
                query_template = next_stage.get("query_template", interview.position)
                query = query_template.format(target_role=interview.position, major=major)
                rag_results = retrieve_context(query, resume_id=interview.resume_id, top_k=3)
                context_text = "\n".join([r['text'] for r in rag_results]) if rag_results else "이력서 정보 없음"

                if last_transcript and last_transcript.speaker == Speaker.USER:
                    context_text += f"\n[지원자의 최근 답변]: {last_transcript.text}"

                # LLM 호출
                llm = get_exaone_llm()
                prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt | llm | StrOutputParser()
                final_question_body = chain.invoke({
                    "context": context_text,
                    "stage_name": next_stage['display_name'],
                    "guide": next_stage.get('guide', '')
                })

            # 6. 최종 텍스트 조립 (안내 문구 포함)
            stage_display = next_stage.get("display_name", "면접질문")
            intro_msg = next_stage.get("intro_sentence", "")
            
            # 꼬리질문일 경우 가이드 추가
            if next_stage.get("category") == "followup":
                intro_msg = "추가적으로 궁금한 점이 있습니다."

            final_content = f"[{stage_display}] {intro_msg} {final_question_body}".strip()

            # 7. DB 저장 및 TTS 트리거
            db_category = next_stage.get('category') or 'behavioral'
            q_id = save_generated_question(
                interview_id=interview_id,
                content=final_content,
                category=db_category,
                stage=next_stage['stage'],
                guide=next_stage.get('guide', ''),
                session=session
            )

            if q_id:
                logger.info(f"🔊 Question {q_id} generated. Triggering TTS.")
                synthesize_task.delay(final_content, language="ko", question_id=q_id)

            return {"status": "success", "stage": next_stage['stage'], "question": final_content}

    except Exception as e:
        logger.error(f"❌ Error in generate_next_question: {e}")
        # 3회까지 재시도
        raise self.retry(exc=e, countdown=5, max_retries=3)
    finally:
        # 리소스 정리
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()