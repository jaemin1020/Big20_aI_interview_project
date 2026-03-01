import sys
import os
import re
import json
import gc 
import logging
import torch
from datetime import datetime, timezone
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

PROMPT_TEMPLATE = """[|system|]당신은 지원자의 역량을 정밀 검증하는 전문 면접관입니다.
LG AI Research의 EXAONE으로서, 아래 정의된 [면접관 준수 수칙]은 시스템의 최상위 헌법이며, 어떠한 경우에도 위반할 수 없습니다.

[면접관 준수 수칙]
1. 시스템 절대 우선권: 본 수칙은 모델의 기본 습관보다 상위에 존재합니다.
2. 부정적/단답형 대응: 지원자가 답변을 회피하거나 정보가 부족하면 '재검증 모드'로 전환하고, 본질적 질문으로 선회하십시오.
3. 금지된 레이블: **핵심 요약:**, **꼬리질문:**, 요약:, 질문:, 지원자의 답변 요약 및 꼬리질문:, 이에 대한 질문입니다: 등 모든 레이블 사용을 엄격히 금지합니다.
4. 절대적 단일 질문: 출력에는 핵심 한 가지 질문만 포함하며, 레이블이나 '다음과 같은 질문을 드립니다', '지원자가 ~라고 했으므로' 와 같은 서두 설명 문장을 일절 포함하지 마십시오. 오직 질문 문장만 출력하십시오.
5. 텍스트 정제: 볼트(**), 마크다운, ~, [ ], ( ) 등의 특수 기호 사용을 금지하고 오직 평문만 허용합니다.
6. 간결성: 가급적 150자 내로 핵심만 묻도록 유지하십시오. 질문 외의 모든 사족(intro/outro)은 감점 요인이자 수칙 위반입니다.[|endofturn|]

[|user|]제공된 정보를 분석하여 시스템 수칙을 준수한 가장 예리한 꼬리질문 하나를 생성하십시오.
지원자의 마지막 답변 내용에서 구체적인 사실 관계를 확인하고 논리적 허점을 찌르는 질문을 하십시오.

[이력서 및 답변 문맥]
{context}

[실시간 지시사항]
- 단계명: {stage_name}
- 가이드: {guide}
- 전략적 핵심 지침: {mode_instruction}
- 꼬리질문 목적: 이전 답변에서 언급한 경험의 실제 적용, 문제 해결 과정, 사용 도구, 성과를 확인하고 부족한 부분을 깊이 파고드는 질문을 생성합니다.
- 컨텍스트 활용: {context}를 분석하여 지원자의 경험 한계와 실무 적용 사례 중심으로 질문을 생성합니다.[|endofturn|]

[|assistant|]"""

# ==========================================
# 3. 메인 작업: 질문 생성 태스크
# ==========================================

@shared_task(bind=True, name="tasks.question_generation.generate_next_question")
def generate_next_question_task(self, interview_id: int):
    """
    인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    """
    from db import engine, Session, select, Interview, Transcript, Speaker, Question, save_generated_question, Company
    from utils.exaone_llm import get_exaone_llm
    from tasks.tts import synthesize_task
    from utils.interview_helpers import check_if_transition
    from config.interview_scenario import get_next_stage as get_next_stage_normal
    from config.interview_scenario_transition import get_next_stage as get_next_stage_transition
    from tasks.rag_retrieval import retrieve_context, retrieve_similar_questions
    try:
        with Session(engine) as session:
            interview = session.get(Interview, interview_id)
            if not interview: 
                logger.error(f"Interview {interview_id} not found.")
                return {"status": "error", "message": "Interview not found"}

            # 2. 마지막 발화 확인 및 Stage 판별
            # [수정] 마지막 발화 확인 (Order 필드 대신 ID/시간순으로 변경하여 정합성 확보)
            stmt_all = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.id.desc())
            last_transcript = session.exec(stmt_all).first()

            # 마지막 AI 발화 가져오기
            stmt_ai = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == Speaker.AI
            ).order_by(Transcript.id.desc())
            last_ai_transcript = session.exec(stmt_ai).first()

            # 마지막 사용자 발화 가져오기 (단, 아주 짧은 노이즈는 무시하여 스테이지 스킵 방지)
            from sqlalchemy import func
            stmt_user = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker != Speaker.AI,
                func.length(Transcript.text) > 5  # 최소 6자 이상인 경우만 실제 답변으로 간주하여 스테이지 전환 판단
            ).order_by(Transcript.id.desc())
            last_user_transcript = session.exec(stmt_user).first()

            # 만약 위에서 못찾았다면 진짜 마지막 발화라도 가져옴 (대기 로직용)
            if not last_user_transcript:
                stmt_user_any = select(Transcript).where(
                    Transcript.interview_id == interview_id,
                    Transcript.speaker != Speaker.AI
                ).order_by(Transcript.id.desc())
                last_user_transcript = session.exec(stmt_user_any).first()

            # [삭제] 10초 이내 스킵 로직 (Race Condition 방지 목적이었으나 초기 템플릿 로드 시 방해됨)

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
                
                # [복구 로직] 만약 마지막 스테이지가 'fallback' 이라면, 그 이전의 정상적인 스테이지를 찾아야 함
                if last_stage_name == "fallback":
                    logger.warning(f"⚠️ Last stage was 'fallback'. Searching for previous valid stage for Interview {interview_id}.")
                    stmt_ai_prev = select(Transcript).where(
                        Transcript.interview_id == interview_id,
                        Transcript.speaker == Speaker.AI,
                        Transcript.id < last_ai_transcript.id
                    ).order_by(Transcript.id.desc())
                    prev_ai = session.exec(stmt_ai_prev).first()
                    if prev_ai and prev_ai.question_id:
                        prev_q = session.get(Question, prev_ai.question_id)
                        if prev_q and prev_q.question_type and prev_q.question_type != "fallback":
                            last_stage_name = prev_q.question_type
                            logger.info(f"🔄 Recovered stage from fallback: {last_stage_name}")
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

            # [수정] 동기화 및 스테이지 스킵 방지 로직 강화
            if last_ai_transcript and last_user_transcript:
                # 1. 만약 마지막 AI 질문이 방금 전(3초 이내)에 던져졌다면, 사용자 답변이 충분히 길지 않은 이상 다음 단계로 넘어가지 않음
                #    (음성 인식 지연/지터로 인해 이전 답변이 새 질문 ID에 꽂히는 현상 방지)
                time_since_ai = (get_kst_now() - last_ai_transcript.timestamp.replace(tzinfo=None)).total_seconds()
                is_short_answer = len(last_user_transcript.text.strip()) < 10
                
                if time_since_ai < 3.0 and is_short_answer:
                    logger.info(f"AI just spoke {time_since_ai:.1f}s ago. Current user answer is short ('{last_user_transcript.text}'). Waiting for a real answer.")
                    return {"status": "waiting_for_user_to_catch_up"}

                # 2. 마지막 AI 발화가 아직 사용자 답변에 의해 참조되지 않았다면? (즉, 아직 답하지 않은 질문이 있다면)
                if last_user_transcript.question_id != last_ai_transcript.question_id:
                    logger.info(f"AI has already spoken up to stage '{last_stage_name}', but user just answered a previous question. Waiting for user to answer current question.")
                    return {"status": "waiting_for_user_to_catch_up"}

            # [수정] 중복 방지 로직 개선: 이미 생성된 경우 정보를 함께 리턴
            if last_ai_transcript:
                last_q_for_check = session.get(Question, last_ai_transcript.question_id) if last_ai_transcript.question_id else None
                if last_q_for_check and last_q_for_check.question_type == next_stage['stage']:
                    logger.info(f"Next stage '{next_stage['stage']}' already exists. Re-triggering TTS/Broadcast.")
                    # TTS 다시 한 번 찔러줌 (이미 있으면 1초도 안 걸림)
                    synthesize_task.delay(last_ai_transcript.text, language="auto", question_id=last_ai_transcript.question_id)
                    return {
                        "status": "success", 
                        "stage": next_stage['stage'], 
                        "question": last_ai_transcript.text,
                        "question_id": last_ai_transcript.question_id
                    }
            # [수정] 공통 정보 추출 (템플릿/AI/꼬리질문 모두 사용)
            candidate_name = "지원자"
            target_role = interview.position or "해당 직무"
            company_name = "저희 회사"
            company_ideal = "누구나 사용할 수 있는 기술을 통해 사용자의 세계를 확장하고, 새로운 관점과 아이디어로 세상을 풍요롭게 하는 인재" # 기본값

            if interview.resume and interview.resume.structured_data:
                sd = interview.resume.structured_data
                if isinstance(sd, str): sd = json.loads(sd)
                header = sd.get("header", {})
                candidate_name = header.get("name") or header.get("candidate_name") or candidate_name
                target_role = header.get("target_role") or target_role
                company_name = header.get("target_company") or header.get("company") or company_name

            # DB에서 회사의 인재상(ideal) 조회
            db_company = None
            if interview.company_id:
                db_company = session.get(Company, interview.company_id)
            if not db_company and company_name != "저희 회사":
                stmt_co = select(Company).where(Company.company_name == company_name)
                db_company = session.exec(stmt_co).first()
            
            if db_company and db_company.ideal:
                company_ideal = db_company.ideal
                logger.info(f"🏢 Dynamic Talent Image Loaded: {company_ideal[:30]}...")

            # [공통] 카테고리 및 DB 변수 선언 (NameError 방지)
            category_raw = next_stage.get("category", "technical")
            category_map = {"certification": "technical", "project": "technical", "narrative": "behavioral", "problem_solving": "situational"}
            db_category = category_map.get(category_raw, "technical")

            # 4. [최적화] template stage는 RAG/LLM 없이 즉시 포맷
            if next_stage.get("type") == "template":
                cert_list = ""
                act_org, act_role = "관련 기관", "담당 업무"
                proj_org, proj_name = "해당 기관", "수행한 프로젝트"
                
                if interview.resume and interview.resume.structured_data:
                    sd = interview.resume.structured_data
                    if isinstance(sd, str): sd = json.loads(sd)
                    
                    # 1. 자격증 리스트업
                    certs = sd.get("certifications", [])
                    if certs:
                        cert_names = [c.get("title") or c.get("name") for c in certs if (c.get("title") or c.get("name"))]
                        cert_list = ", ".join(cert_names)
                    
                    # 4-1. 경력 (activities)
                    acts = sd.get("activities", [])
                    act_header_kws = ["기간", "역할", "기관", "소속", "장소", "제목", "내용"]
                    for act in acts:
                        tmp_org = act.get("organization") or act.get("name") or ""
                        tmp_role = act.get("role") or act.get("position") or ""
                        if not any(kw in tmp_org for kw in act_header_kws) and not any(kw in tmp_role for kw in act_header_kws):
                            act_org = tmp_org or act_org
                            act_role = tmp_role or act_role
                            break
                    
                    # 4-2. 프로젝트 (projects)
                    projs = sd.get("projects", [])
                    proj_header_kws = ["기간", "제목", "과정명", "기관", "설명", "내용"]
                    for proj in projs:
                        tmp_name = proj.get("title") or proj.get("name") or ""
                        tmp_org = proj.get("organization") or ""
                        if not any(kw in tmp_name for kw in proj_header_kws) and not any(kw in tmp_org for kw in proj_header_kws):
                            proj_name = tmp_name or proj_name
                            proj_org = tmp_org or proj_org
                            break
                
                if not cert_list: cert_list = "관련 자격"

                template_vars = {
                    "candidate_name": candidate_name, 
                    "target_role": target_role, 
                    "company_name": company_name,
                    "company_ideal": company_ideal,
                    "major": major or "해당 전공",
                    "cert_list": cert_list,
                    "act_org": act_org,
                    "act_role": act_role,
                    "proj_org": proj_org,
                    "proj_name": proj_name
                }
                
                tpl = next_stage.get("template", "{candidate_name} 지원자님, 계속해주세요.")
                try:
                    formatted = tpl.format(**template_vars)
                except Exception as e:
                    logger.warning(f"Template formatting error: {e}")
                    for k, v in template_vars.items():
                        tpl = tpl.replace("{" + k + "}", str(v))
                    formatted = tpl

                intro_msg = next_stage.get("intro_sentence", "")
                final_content = f"{intro_msg} {formatted}".strip() if intro_msg else formatted
                # [중요] 템플릿 스테이지에서도 sc를 정의해두어야 아래 정제 로직에서 참조 오류가 안 남
                sc = final_content.strip()
                logger.info(f"Template stage '{next_stage['stage']}' → 즉시 포맷 완료")

            else:
                # category_raw는 위에서 공통으로 정의됨
                
                # [핵심 수정] narrative 카테고리(9-14번)는 이력서 RAG를 건너뛰고 인재상에만 집중
                if next_stage.get("type") == "followup":
                    logger.info("🎯 Follow-up mode: Focusing purely on conversation context.")
                    context_text = f"이전 질문: {last_ai_transcript.text if last_ai_transcript else '없음'}\n"
                    if last_user_transcript:
                        context_text += f"[지원자의 최근 답변]: {last_user_transcript.text}"
                    rag_results = []
                elif category_raw == "narrative":
                    if next_stage.get("stage") == "responsibility":
                        # [특생활용] 11번 책임감/가치관 질문은 이력서(자기소개서) 기반으로 생성
                        logger.info("✨ Responsibility Stage (11): Prioritizing Self-Intro Question 1 for values.")
                        
                        # 1. 구조화된 데이터에서 [질문1] 정밀 탐색
                        values_text = ""
                        try:
                            if interview.resume and interview.resume.structured_data:
                                s_data = interview.resume.structured_data
                                if isinstance(s_data, str): s_data = json.loads(s_data)
                                
                                self_intro_list = s_data.get("self_intro", [])
                                for item in self_intro_list:
                                    q_text = item.get("question", "")
                                    # [개선] 더욱 유연하게 질문1 탐색 (인덱스 또는 키워드)
                                    if "[질문1]" in q_text or "질문 1" in q_text or q_text.startswith("1."):
                                        ans = item.get('answer', '')
                                        if len(ans) > 20: # 최소한의 유의미한 길이
                                            values_text = f"[지원자 자기소개서 질문1 답변]: {ans}"
                                            logger.info("📍 Found Question 1 in Self-Intro.")
                                            break
                                
                                # 만약 질문 1을 못찾았다면, 전체 자소서에서 가치관스러운 문장을 추출 (fallback)
                                if not values_text and self_intro_list:
                                    all_answers = " ".join([i.get("answer", "") for i in self_intro_list if i.get("answer")])
                                    values_text = f"[지원자 자기소개서 요약]: {all_answers[:300]}" # 앞부분 300자라도 제공
                        except Exception as e:
                            logger.error(f"Failed to extract self_intro values: {e}")

                        # 2. RAG 결과와 결합
                        rag_results = retrieve_context("지원자의 근본적인 가치관, 생활 신념, 직업 윤리, 정직함", resume_id=interview.resume_id, top_k=2)
                        rag_context = "\n".join([r['text'] for r in rag_results]) if rag_results else ""
                        
                        context_text = f"{values_text}\n\n[추가 참고 정보]:\n{rag_context}".strip()
                        if not context_text: context_text = "특별한 가치관 정보 없음"
                    else:
                        # 나머지 인재상 기반 질문 단계: 이력서 컨텍스트 비활성화
                        logger.info(f"✨ Narrative mode ({next_stage.get('stage')}): Skipping Resume RAG, focusing strictly on Company Ideal.")
                        context_text = f"회사의 인재상 중심 질문 단계입니다. 지원자의 개별 프로젝트보다는 회사의 가치관 부합 여부를 확인하십시오."
                        rag_results = []
                else:
                    # 일반 기술/경험 질문: 이력서 RAG 수행
                    query_template = next_stage.get("query_template", interview.position)
                    try:
                        query = query_template.format(target_role=target_role, major=major or "")
                    except:
                        query = query_template

                    rag_results = []
                    context_text = ""

                    if category_raw == "certification" and interview.resume and interview.resume.structured_data:
                        # 구조화된 데이터에서 자격증 추출 로직 (생략 방지를 위한 유지)
                        context_text = "지원자가 보유한 자격증 목록:\n" + cert_list
                        rag_results = [{'text': f"보유 자격: {cert_list}"}]
                    else:
                        rag_results = retrieve_context(query, resume_id=interview.resume_id, top_k=3)
                        context_text = "\n".join([r['text'] for r in rag_results]) if rag_results else "특별한 정보 없음"
                        
                    if last_user_transcript:
                        context_text += f"\n[지원자의 최근 답변]: {last_user_transcript.text}"
                    else:
                        context_text += "\n[지원자의 응답 정보가 아직 전달되지 않았습니다.]"

                llm = get_exaone_llm()
                prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt | llm | StrOutputParser()

                # 가이드 내 변수 치환
                guide_raw = next_stage.get('guide', '')
                try:
                    guide_formatted = guide_raw.format(company_ideal=company_ideal)
                except:
                    guide_formatted = guide_raw

                # ── [연속 저점수 감지] 아이스브레킹 난이도 하향 ─────────────────
                LOW_SCORE_THRESHOLD = 60   # 저점수 기준 (0-100점 척도)
                LOW_SCORE_CONSECUTIVE = 3  # 연속 저점수 횟수 임계값

                user_transcripts_scored = session.exec(
                    select(Transcript)
                    .where(
                        Transcript.interview_id == interview_id,
                        Transcript.speaker != Speaker.AI,
                        Transcript.total_score.isnot(None),
                    )
                    .order_by(Transcript.id.desc())
                    .limit(LOW_SCORE_CONSECUTIVE)
                ).all()

                is_low_score_streak = (
                    len(user_transcripts_scored) >= LOW_SCORE_CONSECUTIVE
                    and all(
                        (t.total_score or 0) < LOW_SCORE_THRESHOLD
                        for t in user_transcripts_scored
                    )
                )
                # ──────────────────────────────────────────────────────────────

                # [추가] 단계별 맞춤형 전략 지침 결정 (지원자님 요청 반영)
                mode_instruction = "일반적인 단일 질문 생성을 수행하십시오."
                s_name = next_stage.get('stage', '')
                s_type = next_stage.get('type', '')
                
                if s_name == 'problem_solving':
                    mode_instruction = "이 단계는 7번(문제해결질문)입니다. 질문 과정에서 '그런데' 혹은 '그렇다면'과 같은 접속사를 활용하여 자연스럽게 상황을 제시하되, 반드시 딱 하나의 질문만 던지십시오."
                elif s_name == 'responsibility':
                    mode_instruction = "이 단계는 11번(가치관 질문)입니다. 반드시 인사말 없이 즉시 '자기소개서에 [문구]라고 작성하셨습니다.'로 시작하고, '그렇다면'으로 이어가며 딱 하나의 질문만 던지십시오."
                elif s_name == 'responsibility_followup':
                    mode_instruction = "이 단계는 12번(가치관 심층)입니다. 지원자의 답변을 요약한 뒤 '그런데' 등의 접속사를 사용하여 딱 하나의 질문으로 자연스럽게 연결하십시오."
                elif s_name == 'growth':
                    mode_instruction = "이 단계는 13번(성장가능성)입니다. 핵심 인재상 가치 하나를 선택하여 자연스러운 구어체로 딱 하나의 질문만 던지십시오."
                elif s_name == 'communication':
                    mode_instruction = "이 단계는 9번(협업소통질문)입니다. 인사말이나 상황 설명 없이, 인재상 가치를 바탕으로 지원자의 태도를 확인하는 딱 하나의 질문만 즉시 던지십시오."
                elif s_type == 'followup':
                    mode_instruction = "이 단계는 꼬리질문입니다. 답변 요약과 질문을 하나의 문장으로 결합하여 딱 하나의 질문만 생성하십시오."
                
                # ── [아이스브레킹 주입] 연속 저점수 시 격려 및 난이도 하향 ──────
                if is_low_score_streak:
                    mode_instruction += (
                        " [지원자 지원 모드] 지원자가 여러 차례 답변에 어려움을 겪고 있습니다."
                        " 이번 질문은 난이도를 한 단계 낮추어 생성하십시오."
                        " 반드시 질문 문장 앞에 '천천히 답변하셔도 괜찮습니다, 너무 긴장하지 마세요.' 와 같은"
                        " 자연스러운 격려 문장을 먼저 포함하고, 그 뒤에 쉽고 간결한 질문을 이어가십시오."
                    )
                    logger.info(
                        f"🧊 [ICE-BREAK] {LOW_SCORE_CONSECUTIVE}회 연속 저점수 감지 "
                        f"(기준: {LOW_SCORE_THRESHOLD}점 미만). 난이도 하향 및 격려 멘트 주입."
                    )
                # ──────────────────────────────────────────────────────────────

                # [추가] 지원자의 부정적 답변 감지 및 특수 지시 (무지/회피 대응)
                if last_user_transcript:
                    u_text = last_user_transcript.text.strip()
                    negative_keywords = ["모르겠습니다", "모르겠어요", "아니요", "없습니다", "기억이 안 남", "잘 모름"]
                    if any(kw in u_text for kw in negative_keywords) and len(u_text) < 20:
                        mode_instruction += " [주의: 지원자가 답변을 회피하거나 모르겠다고 했습니다. 무리하게 다음 단계를 칭찬하며 요약하지 말고, 답변이 부족함을 언급(예: '구체적인 설명이 부족하여 아쉽습니다만, 이 부분은 어떠신가요?')하며 다른 방향으로 재질문을 던지십시오.]"

                final_content = chain.invoke({
                    "context": context_text,
                    "stage_name": next_stage['display_name'],
                    "company_ideal": company_ideal,
                    "guide": guide_formatted,
                    "mode_instruction": mode_instruction,
                    "target_role": target_role
                })

                # [초강력 정제 시스템] 사족 및 메타 발화 원천 차단
                def clean_ai_output(text: str, stage_label: str) -> str:
                    # 1. 기본 마크다운 및 따옴표 제거
                    text = text.strip()
                    # 따옴표는 문맥상 필요할 수 있으므로(인용 등), 문장 시작/끝의 따옴표만 조심히 제거하거나 
                    # 전체적으로 제거하되 질문 의미를 해치지 않게 함
                    text = re.sub(r'[\*`]', '', text).strip()
                    
                    # 2. 줄바꿈 기준 분해 및 사족 라인 제거
                    lines = text.split('\n')
                    valid_lines = []
                    # 정제 키워드 확장 (이 문구들이 들어간 '짧은' 라인은 사족일 확률이 높음)
                    meta_kws = ["질문", "제시", "생성", "경우", "답변", "내용", "요약", "수칙", "준수", "면접관", "꼬리질문", "작성하셨습니다", "말씀해 주셨는데요"]
                    
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        
                        # "다음과 같은 질문을~", "~라고 답변했다면" 등 문장형 서두 제거
                        if re.search(r'(다음과\s*같은|제시할\s*수|답변했다면|말했다면|질문해\s*보겠습니다|생성한\s*질문|참고하여\s*질문)', line):
                            if ":" in line:
                                line = line.split(":", 1)[-1].strip()
                            else:
                                continue
                        
                        # 단순 레이블형 또는 스테이지명 서두 제거 (Regex 이스케이프 적용)
                        escaped_label = re.escape(stage_label)
                        line = re.sub(fr'^({escaped_label}|핵심\s*요약|요약|질문|답변|Q|A|꼬리질문|질문 내용|면접관 질문|AI 질문)[:\s\-]*', '', line, flags=re.IGNORECASE)
                        
                        # 문장 도중 혹은 끝에 남은 따옴표 제거 (따옴표 안에 질문이 있는 경우 대비)
                        line = line.replace('"', '').replace("'", "").strip()
                        
                        if line: valid_lines.append(line)
                    
                    combined = " ".join(valid_lines).strip()
                    
                    # 3. [핵심] 문장 끝 사족 제거 (더욱 강력한 패턴)
                    # "라고 ." 또는 "라고 합니다." 등의 꼬리표를 제거
                    # 문장에 물음표가 이미 있다면 그 뒤의 "라고~" 이후는 모두 제거
                    if "?" in combined:
                        parts = combined.split("?", 1)
                        if len(parts) > 1 and any(kw in parts[1] for kw in ["라고", "문구", "질문", "합니다"]):
                            combined = parts[0] + "?"
                    
                    # 정규식으로 한 번 더 미세 조정
                    tail_patterns = [
                        r'\s*라고\s*(합니다|질문합니다|생성했습니다|말했습니다|물었습니다|요약합니다|드립니다)[\.\?]?\s*$',
                        r'\s*라는\s*질문을\s*(제시|생성|드립니다|하겠습니다)[\.\?]?\s*$',
                        r'\s*면접관으로서\s*(질문|조언|물음)[\.\?]?\s*$',
                        r'\s*라고\s*[\.\s]*$',  # "라고 ." 또는 "라고  " 제거
                        r'\s*[\.\s]+라고\s*$'
                    ]
                    for pattern in tail_patterns:
                        combined = re.sub(pattern, '', combined).strip()
                    
                    return combined

                final_content = clean_ai_output(final_content, next_stage.get('display_name', ''))

                intro_tpl = next_stage.get("intro_sentence", "")
                intro_msg = ""
                if next_stage['stage'] == 'skill' and 'cert_name' in intro_tpl:
                    cert_name = "자료에 명시된"
                    if rag_results:
                        match = re.search(r'자격명:\s*([^,\(]+)', rag_results[0]['text'])
                        if match: cert_name = match.group(1).strip()
                    intro_msg = intro_tpl.format(candidate_name=candidate_name, cert_name=cert_name)
                elif intro_tpl:
                    try:
                        intro_msg = intro_tpl.format(candidate_name=candidate_name)
                    except:
                        intro_msg = intro_tpl
                
                # Follow-up은 intro_sentence를 무시하는 경향이 있으나 필요시 결합
                if next_stage.get("type") == "followup":
                    # 팔로업은 흐름상 인트로를 최소화
                    pass 
                
                final_content = f"{intro_msg} {final_content}".strip() if intro_msg else final_content.strip()
                sc = final_content.strip() if final_content else ""
                if len(sc) < 10:
                    logger.warning(f"⚠️ [Empty/Short Question Detected] Stage: {next_stage['stage']}, Content: '{final_content}'")
                    if not sc:
                        s_name = next_stage.get('stage', '')
                        if s_name == 'communication':
                            final_content = "팀 프로젝트를 수행하며 의견 차이가 생겼을 때, 본인만의 방식으로 갈등을 조율하여 해결했던 경험이 있다면 구체적으로 말씀해 주시겠습니까?"
                        elif s_name == 'growth':
                            final_content = "지원자님께서 지금까지 성장해 오면서 가장 중요하게 생각하는 삶의 가치나 철학은 무엇인지 말씀해 주시겠습니까?"
                        else:
                            final_content = "지원자님, 해당 부분에 대해 조금 더 구체적으로 설명해 주시겠습니까?"

            # [전역 정제] 모든 질문 타입에 대해 특수문자 제거 및 정제 수행
            final_content = final_content.strip()
            # 콤마(,), 물음표(?), 마침표(.), 느낌표(!), 괄호(()), 따옴표(", '), 물결(~) 등을 허용하도록 확장
            final_content = re.sub(r'[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9\s,\?\.\!\(\)\~\"\'\:]', '', final_content)
            
            # [강력 제약] 만약 정제 과정에서 내용이 사라졌거나 너무 짧은 경우 폴백
            # 공백 제외 실질적인 텍스트 길이를 기준으로 판단
            sc = final_content.strip()
            if len(sc) < 15:
                logger.warning(f"⚠️ [Short Question Detected] Stage: {next_stage['stage']}, Content: '{final_content}'")
                s_name = next_stage.get('stage', '')
                if s_name == 'skill':
                    final_content = "지원자님께서 보유하신 직무 관련 자격이나 기술 중에서, 실제 업무에 가장 큰 도움이 될 것이라고 생각하는 것은 무엇입니까?"
                elif s_name == 'experience':
                    final_content = "실행하신 프로젝트나 업무 경험 중에서, 본인이 가장 주도적으로 참여하여 성과를 냈던 사례에 대해 자세히 말씀해 주시겠습니까?"
                elif s_name == 'experience_followup':
                    final_content = "지원자님, 해당 경험을 통해 기술적으로 가장 크게 성장했다고 느끼신 부분은 무엇인지 조금 더 구체적으로 말씀해 주세요."
                elif s_name == 'problem_solving':
                    final_content = "팀 프로젝트를 수행하며 어려움이 있었을 때, 이를 어떻게 해결하고 목표를 달성하셨는지 구체적으로 말씀해 주시기 바랍니다."
                elif s_name == 'problem_solving_followup' or s_name == 'problem_solving_deep':
                    final_content = "그 과정에서 발생한 예상치 못한 변수를 어떻게 관리하셨는지, 그리고 그 결과에서 얻은 교훈은 무엇인가요?"
                elif s_name == 'communication':
                    final_content = "팀원들과 의견 차이가 생겼을 때, 본인만의 방식으로 조율하여 원만하게 해결했던 경험이 있다면 말씀해 주시겠습니까?"
                elif s_name == 'communication_followup':
                    final_content = "당시 본인의 의견을 관철시키기보다는 팀의 목표를 위해 양보하거나 협협했던 구체적인 사례가 있다면 설명해 주세요."
                elif s_name == 'responsibility':
                    final_content = "지원자님의 가치관과 책임감을 엿볼 수 있는 가장 대표적인 경험 하나를 선정하여 자세히 설명해 주세요."
                elif s_name == 'responsibility_followup':
                    final_content = "지원자님, 그런 상황에서 본인의 가치관을 지키기 위해 가장 중요하게 고려해야 할 점은 무엇이라고 생각하시나요?"
                elif s_name == 'growth':
                    final_content = "지원자님께서 지금까지 성장해 오면서 가장 중요하게 생각하는 삶의 가치나 철학은 무엇인지 말씀해 주시겠습니까?"
                elif s_name == 'growth_followup':
                    final_content = "지원자님, 배움의 과정에서 본인의 목표가 뜻대로 되지 않을 때 이를 극복하고 꾸준히 나아가는 본인만의 원동력은 무엇인가요?"
                elif s_name == 'final_statement':
                    final_content = "지원자님, 마지막으로 꼭 하고 싶으신 말씀이나 본인을 어필할 수 있는 한 마디가 있다면 부탁드립니다."
                elif next_stage.get("type") == "followup":
                    final_content = "지원자님의 답변 내용을 잘 들어보았습니다. 그 과정에서 가장 큰 배움을 얻거나 깨달았던 점은 무엇이었는지 조금 더 구체적으로 설명해 주시겠습니까?"
                else:
                    final_content = "지원자님의 소중한 답변 감사합니다. 다음 질문으로 넘어가기 전, 본인의 강점에 대해 한 가지만 더 구체적으로 말씀해 주시겠습니까?"
            
            final_content = final_content.strip()
            
            # [최종 백지 방지] 만약 여기까지 왔는데도 비어있다면 강제 폴백 적용 (원인 불명의 빈 문자열 방지)
            if not final_content.strip():
                s_name = next_stage.get('stage', '')
                if s_name == 'skill':
                    final_content = "지원자님께서 보유하신 직무 관련 자격이나 기술 중에서, 실제 업무에 가장 큰 도움이 될 것이라고 생각하는 것은 무엇입니까?"
                elif s_name == 'experience':
                    final_content = "실행하신 프로젝트나 업무 경험 중에서, 본인이 가장 주도적으로 참여하여 성과를 냈던 사례에 대해 자세히 말씀해 주시겠습니까?"
                elif s_name == 'experience_followup':
                    final_content = "지원자님, 해당 경험을 통해 기술적으로 가장 크게 성장했다고 느끼신 부분은 무엇인지 조금 더 구체적으로 말씀해 주세요."
                elif s_name == 'problem_solving':
                    final_content = "팀 프로젝트를 수행하며 어려움이 있었을 때, 이를 어떻게 해결하고 목표를 달성하셨는지 구체적으로 말씀해 주시기 바랍니다."
                elif s_name == 'problem_solving_followup' or s_name == 'problem_solving_deep':
                    final_content = "그 과정에서 발생한 예상치 못한 변수를 어떻게 관리하셨는지, 그리고 그 결과에서 얻은 교훈은 무엇인가요?"
                elif s_name == 'communication':
                    final_content = "팀 프로젝트를 수행하며 의견 차이가 생겼을 때, 본인만의 방식으로 갈등을 조율하여 해결했던 경험이 있다면 구체적으로 말씀해 주시겠습니까?"
                elif s_name == 'communication_followup':
                    final_content = "당시 본인의 의견을 관철시키기보다는 팀의 목표를 위해 양보하거나 협력했던 구체적인 사례가 있다면 설명해 주세요."
                elif s_name == 'responsibility':
                    final_content = "지원자님의 가치관과 책임감을 엿볼 수 있는 가장 대표적인 경험 하나를 선정하여 자세히 설명해 주세요."
                elif s_name == 'responsibility_followup':
                    final_content = "지원자님, 그런 상황에서 본인의 가치관을 지키기 위해 가장 중요하게 고려해야 할 점은 무엇이라고 생각하시나요?"
                elif s_name == 'growth':
                    final_content = "지원자님께서 지금까지 성장해 오면서 가장 중요하게 생각하는 삶의 가치나 철학은 무엇인지 말씀해 주시겠습니까?"
                elif s_name == 'growth_followup':
                    final_content = "지원자님, 배움의 과정에서 본인의 목표가 뜻대로 되지 않을 때 이를 극복하고 꾸준히 나아가는 본인만의 원동력은 무엇인가요?"
                elif s_name == 'final_statement':
                    final_content = "지원자님, 마지막으로 꼭 하고 싶으신 말씀이나 본인을 어필할 수 있는 한 마디가 있다면 부탁드립니다."
                else:
                    final_content = "지원자님의 답변을 신중하게 경청했습니다. 해당 부분에 대해 조금 더 구체적으로 말씀해 주시겠습니까?"

            # [문장 부호 최종 정제] .? -> . / ?. -> . / ?? -> ? / .. -> . 등 중복 및 혼용 제거 (사용자 요청: 마침표 유지)
            final_content = final_content.strip()
            
            # 마침표 뒤에 바로 글자가 오는 경우 띄어쓰기 추가 (가독성)
            final_content = re.sub(r'\.([가-힣])', r'. \1', final_content)

            # 마침표와 물음표가 섞여 있으면 마침표를 우선순위로 하여 하나만 남김
            final_content = re.sub(r'[\.\s]+\?+', '.', final_content)  # ". ?" 또는 ".?" -> "."
            final_content = re.sub(r'\?+[\.\s]+', '.', final_content)  # "?." 또는 "? ." -> "."
            final_content = re.sub(r'\?+', '?', final_content)         # "??" -> "?"
            final_content = re.sub(r'\.+', '.', final_content)          # ".." -> "."
            
            # 한 번 더 공백 정리
            final_content = re.sub(r'\s+', ' ', final_content).strip()

            # 7. DB 저장 (Question 및 Transcript)
                # db_category는 최상단에서 이미 정의됨

            logger.info(f"💾 Saving generated question to DB for Interview {interview_id} (Stage: {next_stage['stage']})")
            q_id = save_generated_question(
                interview_id=interview_id,
                content=final_content,
                category=db_category,
                stage=next_stage['stage'],
                guide=next_stage.get('guide', ''),
                session=session
            )

            # 8. 메모리 정리 (더 강력하게)
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                with torch.cuda.device(torch.cuda.current_device()):
                    torch.cuda.empty_cache()
            
            logger.info(f"✅ [SUCCESS] Next question generated for Interview {interview_id}: {final_content[:50]}...")

            # 9. TTS 생성 태스크 즉시 트리거
            if q_id:
                import pathlib
                tts_file = pathlib.Path(f"/app/uploads/tts/q_{q_id}.wav")
                if not tts_file.exists():
                    clean_text = final_content
                    if final_content.startswith('[') and ']' in final_content:
                        clean_text = final_content.split(']', 1)[-1].strip()
                    logger.info(f"🔊 Triggering TTS synthesis for Question ID: {q_id}")
                    synthesize_task.delay(clean_text, language="ko", question_id=q_id)
                else:
                    logger.info(f"🔊 TTS file already exists for Question ID: {q_id}, skipping.")

            return {"status": "success", "stage": next_stage['stage'], "question": final_content}
    except Exception as e:
        logger.error(f"❌ 실시간 질문 생성 실패 (Retry: {self.request.retries}/3): {e}")
        if self.request.retries >= 3:
            logger.warning("⚠️ 질문 생성 최대 재시도 횟수 초과. 스테이지별 폴백 질문을 생성합니다.")
            try:
                from db import save_generated_question
                from tasks.tts import synthesize_task
                with Session(engine) as session:
                    # 현재 스테이지에 맞는 질문 선택 (같은 질문 반복 방지)
                    s_name = next_stage['stage'] if 'next_stage' in locals() and next_stage else ""
                    fallback_dict = {
                        "skill": "지원자님께서 보유하신 직무 기술 중, 실제 업무에서 가장 자신 있게 활용할 수 있는 부분은 무엇입니까?",
                        "skill_followup": "앞선 답변에 대해 조금 더 구체적으로 설명해 주시겠습니까?",
                        "experience": "수행하신 프로젝트나 활동 중에서 본인이 가장 큰 기여를 했던 사례를 하나 말씀해 주세요.",
                        "experience_followup": "그 과정에서 가장 어려웠던 점은 무엇이었고, 어떻게 대처하셨나요?",
                        "problem_solving": "기술적인 문제를 해결하며 가장 보람찼던 순간은 언제입니까?",
                        "problem_solving_followup": "그 판단을 내릴 때 가장 중요하게 고려한 기준은 무엇이었나요?",
                        "communication": "팀원들과 협업할 때 본인만의 소통 방식이나 철학은 무엇인가요?",
                        "communication_followup": "의견 차이가 생겼을 때 본인은 주로 어떻게 해결하십니까?",
                        "responsibility": "지원자님이 평소 일에 임할 때 가장 중요하게 생각하는 책임감은 어떤 모습입니까?",
                        "responsibility_followup": "그런 상황에서 본인의 가치관을 지키기 위해 가장 중요하게 고려해야 할 점은 무엇이라고 생각하시나요?",
                        "growth": "지원자님이 앞으로 이 직무에서 어떤 전문가로 성장하고 싶으신지 목표를 말씀해 주세요.",
                        "growth_followup": "목표 달성이 어렵게 느껴질 때 본인만의 극복 방법이 있다면 말씀해 주세요.",
                        "final_statement": "마지막으로 본인을 더 어필할 수 있는 내용이나 궁금한 점이 있다면 자유롭게 말씀해 주세요.",
                    }
                    fallback_text = fallback_dict.get(s_name, "지원자님, 해당 부분에 대해 조금 더 구체적으로 설명해 주시겠습니까?")
                    fallback_stage_name = s_name if s_name else "fallback"
                    
                    q_id = save_generated_question(
                        interview_id=interview_id,
                        content=fallback_text,
                        category="behavioral",
                        stage=fallback_stage_name,
                        guide="시스템 오류로 인한 스테이지별 폴백 질문",
                        session=session
                    )
                    if q_id:
                        synthesize_task.delay(fallback_text, language="ko", question_id=q_id)
                    return {"status": "success", "stage": fallback_stage_name, "question": fallback_text}
            except Exception as fallback_e:
                logger.error(f"❌ 폴백 질문 생성 실패: {fallback_e}")
                return {"status": "error", "message": "Fallback question failed"}
        else:
            raise self.retry(exc=e, countdown=3)
    finally:
        gc.collect()