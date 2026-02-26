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
LG AI Research의 EXAONE으로서, 아래 정의된 [면접관 준수 수칙]은 이 시스템의 최상위 헌법이며, 어떠한 경우에도 이를 위반할 수 없습니다.

[면접관 준수 수칙]
1. **시스템 절대 우선권**: 본 수칙은 모델의 기본 습관보다 상위에 존재합니다. 하단 [실시간 지시사항]을 시스템의 명령으로 간주하여 100% 이행하십시오.
2. **부정적/단답형 대응 (Negative Answer Handling)**: 지원자가 "모르겠습니다", "아니요", "기억나지 않습니다" 등 답변을 회피하거나 정보가 없는 답변을 한 경우, **[가이드]의 흐름을 끊고 '재검증 모드'로 전환하십시오.** 답변이 부족함을 부드럽지만 단호하게 언급하고, 관련 질문을 다른 방식으로 다시 던지거나 본질을 파고드는 질문으로 선회하십시오.
3. **금지된 레이블 (No Labels)**: '요약:', '질문:', 'Q:', 'A:' 등 어떠한 구분용 레이블도 사용하지 마십시오. 오직 사람이 말하는 대사만 출력하십시오.
4. **절대적 단일 질문 (Single Sentence Priority)**: 문장은 반드시 **단 하나**의 예리한 질문으로 끝나야 합니다. 접속사를 사용하여 두 번째 질문을 생성하거나 화제를 확장하지 마십시오.
5. **텍스트 정제 (Forbidden Markdown)**: 볼트(**), 이탤릭(*) 등 마크다운을 절대 금지합니다. 순수한 평문(Plain Text)만 허용합니다. 
6. **자연스러운 연결**: 요약/인용부와 질문부 사이를 자연스러운 접속어(그렇다면, 그런데 등)로 연결하여 한 호흡의 문장을 만드십시오.
7. **간결성**: 전체 답변은 150자 이내로 명확하게 유지하십시오.[|endofturn|]
[|user|]제공된 정보를 분석하여 시스템 수칙을 준수한 가장 예리한 질문 하나만 생성하십시오.

[이력서 및 답변 문맥]
{context}

[실시간 지시사항]
- 단계명: {stage_name}
- 가이드: {guide}
- 전략적 핵심 지침: {mode_instruction}[|endofturn|]
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

            stmt_ai = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == Speaker.AI
            ).order_by(Transcript.id.desc())
            last_ai_transcript = session.exec(stmt_ai).first()

            stmt_user = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == Speaker.USER
            ).order_by(Transcript.id.desc())
            last_user_transcript = session.exec(stmt_user).first()

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

            # [수정] 동기화 로직: 이미 AI가 다음 질문(들)을 던졌는데 사용자가 아직 이전 질문에 답하는 중이라면 대기
            if last_ai_transcript and last_user_transcript:
                # 마지막 AI 발화가 아직 사용자 답변에 의해 참조되지 않았다면? (즉, 아직 답하지 않은 질문이 있다면)
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
                display_name = next_stage.get("display_name", "면접질문")
                final_content = f"[{display_name}] {intro_msg} {formatted}".strip() if intro_msg else f"[{display_name}] {formatted}"
                logger.info(f"Template stage '{next_stage['stage']}' → 즉시 포맷 완료")

            else:
                category_raw = next_stage.get("category")
                
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
                                    if "[질문1]" in item.get("question", ""):
                                        values_text = f"[지원자 자기소개서 질문1 답변]: {item.get('answer', '')}"
                                        logger.info("📍 Found Question 1 in Self-Intro.")
                                        break
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
                s_name = next_stage.get('stage', '')
                s_type = next_stage.get('type', '')
                
                if s_name == 'responsibility':
                    mode_instruction = "이 단계는 11번(가치관 질문)입니다. 반드시 인사말 없이 즉시 '자기소개서에 [문구]라고 작성하셨습니다.'로 시작하십시오."
                elif s_name == 'growth':
                    mode_instruction = "이 단계는 13번(성장가능성)입니다. 회사의 모든 인재상을 나열하지 말고, 가장 핵심적인 가치 하나만 선택하여 지원자의 일상적 도전과 연결하십시오. '설명해 주시겠습니까?' 같은 딱딱한 표현 대신 '어떤 노력을 하시나요?' 또는 '어떻게 대처하시나요?'와 같이 자연스러운 구어체로 질문하십시오."
                elif s_type == 'followup':
                    mode_instruction = "이 단계는 꼬리질문입니다. 지원자의 답변을 짧게 요약한 뒤 '그런데', '하지만' 등의 접속사를 사용하여 질문을 자연스럽게 이어가십시오. 절대로 '요약:' 같은 레이블을 쓰지 마십시오."
                
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

                # [정제]
                final_content = final_content.strip()
                final_content = re.sub(r'^["\'\s]+|["\'\s]+$', '', final_content)
                final_content = re.sub(r'^(\'?\d+\.|\'?질문:|\'?Q:|\'?-\s*)\s*', '', final_content)
                final_content = final_content.strip()

                intro_tpl = next_stage.get("intro_sentence", "")
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
                else:
                    intro_msg = ""

                if next_stage.get("type") == "followup":
                    intro_msg = "" 
                
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

            # 8. TTS 생성 태스크 즉시 트리거 (중복 방지: 파일 존재 확인)
            if q_id:
                import pathlib
                tts_file = pathlib.Path(f"/app/uploads/tts/q_{q_id}.wav")
                if not tts_file.exists():
                    # [단계] 태그 제거 (TTS가 읽는 클린 텍스트)
                    clean_text = final_content
                    if final_content.startswith('[') and ']' in final_content:
                        clean_text = final_content.split(']', 1)[-1].strip()
                    logger.info(f"🔊 Triggering TTS synthesis for Question ID: {q_id}")
                    synthesize_task.delay(clean_text, language="ko", question_id=q_id)
                else:
                    logger.info(f"🔊 TTS file already exists for Question ID: {q_id}, skipping.")

            return {"status": "success", "stage": next_stage['stage'], "question": final_content}
    except Exception as e:
        logger.error(f"❌ 실시간 질문 생성 실패 (Retry 시도): {e}")
        raise self.retry(exc=e, countdown=3)
    finally:
        gc.collect()