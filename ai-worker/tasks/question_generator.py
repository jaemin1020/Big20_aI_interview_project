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

def is_meaningless(text: str) -> bool:
    """지원자의 답변이 무의미한지(자음 나열, 너무 짧음 등) 체크합니다."""
    if not text: return True
    text = text.strip()
    # 1. 너무 짧음 (5자 미만)
    if len(text) < 5: return True
    # 2. 자음/모음만 나열 (ㄴㅇㄹㄴㅇㄹ, ㅋㅋㅋㅋ 등)
    if re.fullmatch(r'[ㄱ-ㅎㅏ-ㅣ\s]+', text): return True
    # 3. 단순 특수문자/숫자 반복 (...., 123123 등)
    if re.fullmatch(r'[\.\,\!\?\-\=\s\d]+', text): return True
    # 4. 영어 랜덤 문자열 (asdf, qwer 등)
    if re.fullmatch(r'[a-zA-Z]{1,5}', text): return True
    return False

# ==========================================
# 2. 페르소나 설정 (Prompt Engineering)
# ==========================================
PROMPT_TEMPLATE = """[|user|]당신은 전문적인 지식과 공정한 태도를 겸비한 베테랑 AI 면접관입니다.
다음 지침에 따라 지원자의 잠재력을 예리하게 파악할 수 있는 **단 하나의 질문**을 생성하십시오.

### [면접 전략 및 페르소나]
- 평가 대상 직무: {target_role}
- 핵심 인재상: {company_ideal}
- 면접 단계: {stage_name} ({guide})

### [참고 문맥: 지원자 정보 및 이전 답변]
{context}

### [실시간 핵심 임무]
- 수행 과업: {mode_task_instruction}
- 실행 상세: {mode_instruction}
- 전역 제약: {global_constraint}

### [출력 규칙 - 반드시 준수]
1. 인사말, 부연 설명, 자기소개, 가설 제시를 절대 하지 마십시오.
2. "질문입니다", "다음 질문은" 등 서두를 일절 붙이지 마십시오.
3. 오직 지원자에게 직접 던지는 **물음표(?)로 끝나는 단일 문장의 질문**만 출력하십시오.
4. 전문적인 한국어 구어체(하십시오체)를 사용하십시오.[|endofturn|]
[|assistant|]"""

# ==========================================
# 3. 모델 사전 로딩 및 메인 작업
# ==========================================

@shared_task(name="tasks.question_generation.preload_model")
def preload_model_task():
    """
    EXAONE 모델을 비동기로 미리 로드합니다. (면접 시작 시 호출)
    """
    from utils.exaone_llm import get_exaone_llm
    try:
        logger.info("🔥 [Preload] Starting EXAONE model preloading...")
        get_exaone_llm() # 싱글톤 인스턴스 생성 시 모델 로드됨
        logger.info("✅ [Preload] EXAONE model preloaded inside Celery worker.")
        return {"status": "success", "message": "Model preloaded"}
    except Exception as e:
        logger.error(f"❌ [Preload] Failed to preload model: {e}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, name="tasks.question_generation.generate_next_question")
def generate_next_question_task(self, interview_id: int):
    """
    인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    """
    from db import engine, Session, select, Interview, Transcript, Speaker, Question, save_generated_question, Company, get_kst_now
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

            # 마지막 사용자 발화 가져오기 (단, 아주 짧은 노이즈는 무시하되 1자 이상이면 답변으로 인정)
            from sqlalchemy import func
            stmt_user = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker != Speaker.AI,
                func.length(Transcript.text) >= 1  # 1자 이상이면 실제 답변으로 간주
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
                        # [개선] 9-14번 인성 면접: 각 역량(협업, 성장, 책임감)에 특화된 RAG 수행
                        s_name = next_stage.get('stage', '')
                        behavioral_keywords = {
                            "communication": "협업 사례, 팀 프로젝트 중 갈등 조율, 팀워크 발휘, 소통 능력",
                            "growth": "자기계발 노력, 새로운 기술 학습 태도, 실패 극복 및 성장 사례",
                            "responsibility": "직업 윤리, 약속 이행, 정직함과 관련된 경험"
                        }
                        # 해당 단계에 맞는 쿼리 선택 (없으면 기본 가치관 경험 검색)
                        target_query = behavioral_keywords.get(s_name, "본인의 강점, 성취감, 도전적인 경험 사례")
                        
                        logger.info(f"✨ Behavioral RAG ({s_name}): Searching for '{target_query}'")
                        rag_results = retrieve_context(target_query, resume_id=interview.resume_id, top_k=2)
                        rag_context = "\n".join([r['text'] for r in rag_results]) if rag_results else ""
                        
                        context_text = (
                            f"이 단계는 {next_stage['display_name']}를 확인하는 인성 면접입니다.\n"
                            f"지원자의 기술력 검증보다는 **태도, 가치관, 조직 적응력**을 파악하는 데 집중하십시오.\n"
                            f"아래 [지원자 경험 정보]를 '배경'으로 활용하여 구체적인 질문을 생성하십시오.\n\n"
                            f"[지원자 경험 정보]:\n{rag_context}"
                        )
                else:
                    # 일반 기술/경험 기반 질문 (4, 5, 8번 등 새로운 주제 시작 시)
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
                        context_text = "\n".join([r['text'] for r in rag_results]) if rag_results else "특별한 정보 없음"
                        
                    if last_user_transcript:
                        # [전략 4] 무의미한 답변일 경우 이전 컨텍스트를 삭제하여 환각 방어
                        if is_meaningless(last_user_transcript.text):
                             context_text = "[주의: 지원자의 이전 답변이 무의미하거나 누락되었습니다. 과거 정보에 의존하지 말고 다시 물어보십시오.]"
                             logger.warning("🚫 Meaningless input detected! Isolating context to prevent hallucination.")
                        
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

                # [추가] 단계별 맞춤형 전략 지침 결정 (지원자님 요청 반영)
                mode_instruction = "일반적인 단일 질문 생성을 수행하십시오."
                mode_task_instruction = "제공된 정보를 분석하여 가장 예리한 꼬리질문 하나를 생성하십시오. 지원자의 마지막 답변 내용에서 구체적인 사실 관계를 확인하고 논리적 허점을 찌르는 질문을 하십시오." # 기본값
                global_constraint = "오직 질문만을 생성하고, 기술 스택과 수치를 적절히 인용하십시오." # 기본 기술 지침
                
                s_name = next_stage.get('stage', '')
                s_type = next_stage.get('type', '')
                
                # 인성 면접 단계(9~14) 여부 확인
                is_narrative = (next_stage.get('category') == 'narrative') or (s_name in ['communication', 'communication_followup', 'responsibility', 'responsibility_followup', 'growth', 'growth_followup'])

                if is_narrative:
                    global_constraint = "인성 단계입니다. **코드, 설계, 개발과 같은 직무 단어를 사용하지 말고**, 태도와 가치관을 인용하여 짧게 질문하십시오."
                
                if s_name == 'problem_solving':
                    mode_instruction = "이 단계는 7번(문제해결질문)입니다. 질문 과정에서 '그런데' 혹은 '그렇다면'과 같은 접속사를 활용하여 자연스럽게 상황을 제시하되, 반드시 딱 하나의 질문만 던지십시오."
                elif s_name == 'responsibility':
                    # 11번 가치관 질문: 기술 중심 인용 대신 가치 중심 전환 (전체 길이 30% 축소)
                    mode_task_instruction = "자기소개서에서 나타난 지원자의 핵심 가치관(정직, 책임감 등)을 파악하여 인재상과 연결하십시오. 서비스 설계나 코드 같은 기술 내용은 일절 언급하지 말고 오직 인성적인 면모를 80자 이내로 물으십시오."
                    mode_instruction = "이전 답변 요약을 생략하고, '자기소개서에서 ~한 가치관이 인상적이었습니다. 그렇다면...'과 같이 자연스럽게 대화하십시오. 30% 더 짧게 생성하십시오."
                elif s_name == 'responsibility_followup':
                    mode_instruction = "이 단계는 12번(가치관 심층)입니다. 지원자의 답변에 실제 내용이 있을 경우에만 아주 짧게 요약하고, 곧바로 가치관에 대한 질문 하나를 던지십시오. 60자 이내로 구성하십시오."
                elif s_name in ['communication', 'growth']:
                    # 9번, 13번 인성 질문: 태도 강조 및 길이 축소
                    mode_task_instruction = "인재상과 이력서를 결합하되, 기술적 성취가 원인이 아닌 '협업 태도'와 '성장 의지'가 질문의 주인공이 되게 하십시오. 모든 문장은 현재보다 30% 더 짧고 간략하게 구성하십시오."
                    mode_instruction = f"이 단계는 {s_name} 검증입니다. 코드, 개발, 스택 같은 단어를 배제하고 대화하듯 딱 하나의 간결한 한 문장으로만 질문하십시오."
                elif s_type == 'followup':
                    mode_instruction = "이 단계는 꼬리질문입니다. 답변 요약과 질문을 하나의 문장으로 결합하여 딱 하나의 질문으로 생성하십시오."
                
                # [추가] 지원자의 부정적 답변 감지 및 특수 지시 (무지/회피 대응)
                if last_user_transcript:
                    u_text = last_user_transcript.text.strip()
                    # "싫다", "몰라" 등 키워드 보강
                    negative_keywords = ["모르겠습니다", "모르겠어요", "아니요", "없습니다", "기억이 안 남", "잘 모름", "몰라요", "몰라", "싫어", "싫음", "싫다"]
                    
                    # [전략 3] 무의미한 입력이거나 명시적 거절일 때 지시어 전환
                    if is_meaningless(u_text) or any(kw in u_text for kw in negative_keywords):
                        mode_task_instruction = "지원자가 답변을 하지 못하거나 의미 없는 입력을 했습니다. 이전 내용에 대한 요약이나 추측을 100% 생략하고, 정중하게 다시 설명을 요청하거나 다른 주제로 전환하십시오."
                        global_constraint = "이전 답변 요약을 **절대** 하지 마십시오. 답변을 지어내지 말고, '알겠습니다. 그렇다면 이번에는...'과 같이 자연스럽게 대화를 이어가십시오."
                        mode_instruction = "환각(Hallucination) 없이 담백하게 다음 질문으로 넘어가거나 재설명을 요청하십시오."

                final_content = chain.invoke({
                    "context": context_text,
                    "stage_name": next_stage['display_name'],
                    "company_ideal": company_ideal,
                    "guide": guide_formatted,
                    "mode_instruction": mode_instruction,
                    "mode_task_instruction": mode_task_instruction,
                    "global_constraint": global_constraint,
                    "target_role": target_role
                })

                # [정제 가속화 및 로직 강화]
                final_content = final_content.strip()
                # 서두/말미 따옴표 제거
                final_content = re.sub(r'^["\'\s“]+|["\'\s”]+$', '', final_content)
                
                # 1. 메타 설명 및 가이드 문구 강제 삭제 (패턴 보강)
                meta_patterns = [
                    r'(그렇다면|따라서|이에|제공된|분석하여)\s*(지원자의|내용을|부족한|부분을|파악하여|탐구할)\s*.*?(제시하겠습니다|드리겠습니다|하겠습니다|질문입니다)[\.\s]*',
                    r'(이\s*질문은|의도는|~라고\s*답변했다면|검증합니다|의도함|확인합니다|요구하여).*', 
                    r'지원자가\s*.*라고\s*말했다면.*',
                    r'위\s*질문은\s*.*',
                    r'본\s*질문은\s*.*'
                ]
                for pattern in meta_patterns:
                    final_content = re.sub(pattern, '', final_content, flags=re.IGNORECASE | re.DOTALL)

                # 2. 서두 레이블 제거 (한글/영문/특수문자 포함)
                label_patterns = [
                    r'^\**지원자의?\s*답변\s*요약\s*(및\s*꼬리질문)?:\**\s*',
                    r'^\**심층\s*질문:\**\s*',
                    r'^\**핵심\s*요약:\**\s*',
                    r'^\**꼬리질문:\**\s*',
                    r'^\**요약:\**\s*',
                    r'^\**질문:\**\s*',
                    r'^\**[QA]:\**\s*',
                    r'^\d+\.\s*',
                    r'^-\s*'
                ]
                for pattern in label_patterns:
                    final_content = re.sub(pattern, '', final_content, flags=re.IGNORECASE | re.MULTILINE)

                # 3. [핵심] 만약 여전히 "요약: ... 질문: ..." 구조라면 '질문:' 이후만 추출
                if '질문:' in final_content:
                    final_content = final_content.split('질문:')[-1].strip()
                elif '질문 :' in final_content:
                    final_content = final_content.split('질문 :')[-1].strip()

                # 3. 문장 중간에 삽입되는 연결 레이블 제거
                bridge_patterns = [
                    r'이에\s*대한\s*질문입니다:?',
                    r'다음은\s*질문입니다:?',
                    r'질문드립니다:?',
                    r'질문은\s*다음과\s*같습니다:?',
                    r'\*\*.*\*\*:\s*' # 볼트가 포함된 모든 레이블 형태 제거
                ]
                for pattern in bridge_patterns:
                    final_content = re.sub(pattern, '', final_content, flags=re.IGNORECASE)

                # 4. Markdown 제목(#) 및 불필요한 태그 제거 (## 제목, [질문레이블] 등)
                final_content = re.sub(r'#+\s*.*?\n', '\n', final_content) # ## 제목 제거
                final_content = re.sub(r'#+\s*.*$', '', final_content)    # 줄 끝의 # 제거
                final_content = re.sub(r'\[.*?질문\]', '', final_content)   # [성장가능성질문] 등 제거
                
                # 5. [핵심] 만약 AI가 "..." 처럼 따옴표 안에 질문을 넣었다면 그것만 추출
                quote_match = re.search(r'["\'“]([^"\'”]*\?+)["\'”]', final_content)
                if quote_match:
                    final_content = quote_match.group(1)

                # 5. [정제 로직 완화] 물음표 자르기를 정교하게 수행 (문맥 보존)
                # 단일 문장만 남기는 대신, 마지막 물음표 이후의 '부연 설명(가이드라인)'만 제거
                # AI가 가끔 말끝에 "이 질문은 ~를 의도함" 등을 붙이는 것 방지
                final_content = final_content.replace("**", "").strip()
                if '?' in final_content:
                    # 패턴 기반: 질문 의도나 설명이 시작되는 키워드가 있으면 그 앞까지만 유지
                    cut_patterns = ["이 질문은", "질문의 의도", "의도는", "답변을 통해", "확인하고자 함", "검증하고자 하는"]
                    for pattern in cut_patterns:
                        if pattern in final_content:
                            final_content = final_content.split(pattern)[0].strip()
                    
                    # 만약 물음표가 있고 그 뒤에 아주 짧은 문장(설명조)이 더 있다면 마지막 물음표까지만 유지
                    q_last_idx = final_content.rfind('?') + 1
                    if q_last_idx < len(final_content) and len(final_content) - q_last_idx < 30:
                        final_content = final_content[:q_last_idx]

                # [완화] 무조건적인 물음표 1개 제한 대신, 너무 여러 개(3개 이상)인 경우만 상위 2개로 제한
                if final_content.count('?') > 2:
                    logger.warning(f"⚠️ Excessive questions detected. Truncating to first two.")
                    q_parts = final_content.split('?')
                    final_content = q_parts[0] + '?' + q_parts[1] + '?'
                
                final_content = final_content.strip()

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