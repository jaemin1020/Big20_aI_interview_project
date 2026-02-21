import sys
import os
import re
import json
import gc 
import logging
import torch
from datetime import datetime
from celery import shared_task
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==========================================
# 1. 초기 설정 및 모델 경로 최적화
# ==========================================

if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# 모델 경로 설정
local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
model_path = docker_path if os.path.exists(docker_path) else local_path

# ==========================================
# 2. 페르소나 설정 (Prompt Engineering)
# ==========================================

PROMPT_TEMPLATE = """[|system|]당신은 지원자의 역량을 정밀하게 검증하는 전문 면접관입니다.
제공된 [이력서 문맥]과 [면접 진행 상황]을 바탕으로, 지원자에게 던질 '다음 질문' 1개만 생성하십시오.

[절대 규칙]
1. 반드시 한국어로 답변하십시오.
2. 질문은 명확하고 구체적이어야 하며, 150자 이내로 작성하십시오.
3. 특수문자(JSON 기호, 역따옴표 등)를 절대 사용하지 마십시오. 오직 순수 텍스트만 출력하십시오.
4. "질문:" 이라는 수식어 없이 바로 질문 본문만 출력하십시오.
5. 이전 질문과 중복되지 않도록 하십시오.
6. **환각 주의**: 이력서에 "익히고 싶다", "공부할 계획이다", "성장하겠다" 등 미래 포부로 적힌 내용은 실제 실무 경험이나 프로젝트 성과로 취급하여 질문하지 마십시오. 미래 포부는 학습 의지나 관심도를 묻는 용도로만 사용하십시오.

[이력서 및 답변 문맥]
{context}

[현재 면접 단계 정보]
- 단계명: {stage_name}
- 가이드: {guide}

[|user|]위 정보를 바탕으로 면접 질문을 생성해 주세요.[|endofturn|]
[|assistant|]"""

# ==========================================
# 3. 메인 작업: 질문 생성 태스크
# ==========================================

@shared_task(name="tasks.question_generation.generate_next_question")
def generate_next_question_task(interview_id: int):
    """
    인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    """
    from db import engine, Session, select, Interview, Transcript, Speaker, Question, save_generated_question
    from utils.exaone_llm import get_exaone_llm
    from tasks.tts import synthesize_task
    from utils.interview_helpers import check_if_transition
    from config.interview_scenario import get_next_stage as get_next_stage_normal
    from config.interview_scenario_transition import get_next_stage as get_next_stage_transition
    from tasks.rag_retrieval import retrieve_context
    try:
        with Session(engine) as session:
            interview = session.get(Interview, interview_id)
            if not interview: 
                logger.error(f"Interview {interview_id} not found.")
                return {"status": "error", "message": "Interview not found"}

            # 2. 마지막 AI 발화 확인 (Stage 판별 + 중복 방지)
            # [수정] User transcript는 question_id가 없어 stage 판별 불가 → 마지막 AI 발화 기준으로 판별
            stmt_all = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order.desc())
            last_transcript = session.exec(stmt_all).first()

            stmt_ai = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == Speaker.AI
            ).order_by(Transcript.order.desc(), Transcript.id.desc())  # id를 tiebreaker로 사용 (order 같을 때 최신 AI 발화 보장)
            last_ai_transcript = session.exec(stmt_ai).first()

            # 마지막 AI 발화가 10초 이내라면 스킵 (Race Condition 방지)
            if last_ai_transcript:
                diff = (datetime.utcnow() - last_ai_transcript.timestamp).total_seconds()
                if diff < 10:
                    logger.info(f"Skipping duplicate request for interview {interview_id}")
                    return {"status": "skipped"}

            # [수정] 3. 전공/직무 기반 시나리오 결정
            major = ""
            if interview.resume and interview.resume.structured_data:
                sd = interview.resume.structured_data
                if isinstance(sd, str):
                    sd = json.loads(sd)
                edu = sd.get("education", [])
                major = next((e.get("major", "") for e in edu if e.get("major", "").strip()), "")

            is_transition = check_if_transition(major, interview.position)
            get_next_stage_func = get_next_stage_transition if is_transition else get_next_stage_normal

            # 마지막 AI 발화의 question_type으로 현재 stage 판별
            if last_ai_transcript and last_ai_transcript.question_id:
                last_question = session.get(Question, last_ai_transcript.question_id)
                last_stage_name = last_question.question_type if last_question else "intro"
            else:
                last_stage_name = "intro"

            logger.info(f"Current stage determined: {last_stage_name} (is_transition={is_transition})")
            next_stage = get_next_stage_func(last_stage_name)

            if not next_stage:
                logger.info(f"Interview {interview_id} finished. Transitioning to COMPLETED.")
                interview.status = "COMPLETED"
                session.add(interview)
                session.commit()
                return {"status": "completed"}

            # [수정] 꼬리질문(followup) 생성 제한 로직
            # 다음 단계가 followup인데, 마지막 발화자가 여전히 AI라면 지원자가 아직 답변을 안 한 것임.
            if next_stage.get("type") == "followup":
                if last_transcript and last_transcript.speaker == "AI":
                    logger.info(f"Next stage is followup, but WAITING for user answer. Skipping generation.")
                    return {"status": "waiting_for_user"}

            # [중복 방지 개선] next_stage가 이미 생성됐는지 확인 (timestamp 기반 X → stage 기반 O)
            if last_ai_transcript:
                last_q_for_check = session.get(Question, last_ai_transcript.question_id) if last_ai_transcript.question_id else None
                if last_q_for_check and last_q_for_check.question_type == next_stage['stage']:
                    diff = (datetime.utcnow() - last_ai_transcript.timestamp).total_seconds()
                    if diff < 30:
                        logger.info(f"Next stage '{next_stage['stage']}' already generated {diff:.1f}s ago, skipping duplicate")
                        return {"status": "skipped"}

            # 4. [최적화] template stage는 RAG/LLM 없이 즉시 포맷
            if next_stage.get("type") == "template":
                candidate_name = "지원자"
                target_role = interview.position or "해당 직무"
                if interview.resume and interview.resume.structured_data:
                    sd = interview.resume.structured_data
                    if isinstance(sd, str):
                        sd = json.loads(sd)
                    candidate_name = sd.get("header", {}).get("name", "지원자")
                    target_role = sd.get("header", {}).get("target_role", target_role)

                template_vars = {"candidate_name": candidate_name, "target_role": target_role, "major": major}
                tpl = next_stage.get("template", "{candidate_name} 지원자님, 계속해주세요.")
                try:
                    formatted = tpl.format(**template_vars)
                except KeyError:
                    formatted = tpl

                intro_msg = next_stage.get("intro_sentence", "")
                display_name = next_stage.get("display_name", "면접질문")
                final_content = f"[{display_name}] {intro_msg} {formatted}".strip() if intro_msg else f"[{display_name}] {formatted}"
                logger.info(f"Template stage '{next_stage['stage']}' → 즉시 포맷 완료 (RAG/LLM 생략)")

            else:
                # 4-b. AI stage: RAG로 문맥 확보 후 LLM 생성
                query_template = next_stage.get("query_template", interview.position)
                try:
                    query = query_template.format(
                        target_role=interview.position or "해당 직무",
                        major=major or ""
                    )
                except (KeyError, ValueError):
                    query = query_template 
                
                # [개선] 카테고리가 'certification'인 경우 자격증(certifications) 섹션만 엄격하게 필터링
                filter_type = None
                category_raw = next_stage.get("category")
                if category_raw == "certification":
                    filter_type = "certifications"
                    logger.info("🎯 Category 'certification' detected: Strict filtering for certifications context.")

                rag_results = retrieve_context(query, resume_id=interview.resume_id, top_k=3, filter_type=filter_type)
                
                # 자격증 카테고리인데 결과가 만약 없다면 전체 섹션에서 재검색
                if not rag_results and filter_type == "certifications":
                    logger.info("⚠️ No exact 'certifications' section found, searching globally for certificates.")
                    rag_results = retrieve_context(f"보유 자격증 자격 취득 {query}", resume_id=interview.resume_id, top_k=3)

                context_text = "\n".join([r['text'] for r in rag_results]) if rag_results else "특별한 정보 없음"

                if last_transcript and last_transcript.speaker == "User":
                    context_text += f"\n[지원자의 최근 답변]: {last_transcript.text}"

                llm = get_exaone_llm()
                prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt | llm | StrOutputParser()

                final_content = chain.invoke({
                    "context": context_text,
                    "stage_name": next_stage['display_name'],
                    "guide": next_stage.get('guide', '')
                })

                # 인트로 메시지 조합 (3번 질문 전용 로직 포함)
                candidate_name = "지원자"
                if interview.resume and interview.resume.structured_data:
                    sd = interview.resume.structured_data
                    if isinstance(sd, str): sd = json.loads(sd)
                    candidate_name = sd.get("header", {}).get("name", "지원자")

                intro_tpl = next_stage.get("intro_sentence", "")
                if next_stage['stage'] == 'skill' and 'cert_name' in intro_tpl:
                    # RAG 결과에서 첫 번째 자격증 이름 추출 시도
                    cert_name = "자료에 명시된"
                    if rag_results:
                        # "[자격증] 자격명: XXX" 형태에서 이름 추출
                        match = re.search(r'자격명:\s*([^,\(]+)', rag_results[0]['text'])
                        if match: cert_name = match.group(1).strip()
                    intro_msg = intro_tpl.format(candidate_name=candidate_name, cert_name=cert_name)
                elif intro_tpl:
                    try:
                        intro_msg = intro_tpl.format(candidate_name=candidate_name)
                    except:
                        intro_msg = intro_tpl
                else:
                    intro_msg = ""

                if next_stage.get("type") == "followup":
                    intro_msg = "답변 감사합니다. 추가적으로 궁금한 점이 있습니다."
                
                display_name = next_stage.get("display_name", "심층 면접")
                final_content = f"[{display_name}] {intro_msg} {final_content}".strip() if intro_msg else f"[{display_name}] {final_content}".strip()

            # 6. DB 저장 (Question 및 Transcript)

            # 6. DB 저장 (Question 및 Transcript)
            category_raw = next_stage.get("category", "technical")
            category_map = {"certification": "technical", "project": "technical", "narrative": "behavioral", "problem_solving": "situational"}
            db_category = category_map.get(category_raw, "technical")

            logger.info(f"💾 Saving generated question to DB for Interview {interview_id} (Stage: {next_stage['stage']})")
            q_id = save_generated_question(
                interview_id=interview_id,
                content=final_content,
                category=db_category,
                stage=next_stage['stage'],
                guide=next_stage.get('guide', ''),
                session=session
            )

            # 7. 메모리 정리
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 8. TTS 생성 태스크 즉시 트리거
            if q_id:
                logger.info(f"🔊 Triggering TTS synthesis for Question ID: {q_id}")
                synthesize_task.delay(final_content, language="auto", question_id=q_id)

            return {"status": "success", "stage": next_stage['stage'], "question": final_content}
    except Exception as e:
        logger.error(f"❌ 실시간 질문 생성 실패 (Retry 시도): {e}")
        raise self.retry(exc=e, countdown=3)
    finally:
        gc.collect()