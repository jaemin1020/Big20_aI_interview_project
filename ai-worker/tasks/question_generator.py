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
import redis

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
 3. 특수문자(JSON 기호, 역따옴표, 작은따옴표 등)를 절대 사용하지 마십시오. 오직 순수 텍스트만 출력하십시오.
 4. 질문 앞머리에 '1.', '질문:' 또는 따옴표(') 등을 절대 붙이지 마십시오. 바로 본문만 시작하십시오.
 5. 이전 질문과 중복되지 않도록 하십시오.
 6. **어조 규칙**: 기본적으로 모든 질문은 '~주세요.'로 끝맺음하고 물음표(?)를 사용하지 마십시오. 단, 별도의 지시가 있는 [가이드]가 제공될 경우 해당 가이드의 어조(예: '~인가요?')와 물음표 사용 유무를 최우선으로 따르십시오.
 7. **꼬리질문(Follow-up) 규칙**: 지원자의 답변 중 핵심적인 구절을 골라 작은따옴표(' ') 안에 넣어 "...라고 하셨는데,"로 요약하며 시작하십시오. (예: 'RAG 아키텍처'라고 말씀하셨는데,)
 8. **심층 질문 전개**: 지원자가 답변한 내용 내에서만 심도 있게 질문하십시오. 외부 지식 인용이나 가짜 경험 조작은 절대 금지입니다. 가이드에서 요청하는 경우 어조를 유연하게 변경하십시오.
 9. **문장 검증(Self-Correction)**: 질문을 출력하기 전, 문장이 비논리적이거나 도중에 끊기지 않았는지, 그리고 질문의 의도가 명확한지 스스로 최종 확인하십시오. 어색한 비문은 자동으로 수정하여 완결된 문장만 출력하십시오.

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

@shared_task(name="tasks.question_generation.preload_model")
def preload_model_task():
    """
    EXAONE 모델을 메모리에 미리 로드해두는 웜업(Warmup) 태스크.
    면접 세션 생성 시 즉시 실행하여, AI 질문이 필요한 시점에 모델이 이미 준비된 상태가 되도록 합니다.
    """
    try:
        from utils.exaone_llm import get_exaone_llm
        logger.info("🔥 [Preload] EXAONE 모델 사전 로딩 시작...")
        get_exaone_llm()  # 싱글톤 - 한 번 로딩되면 이후 태스크에서 재사용
        logger.info("✅ [Preload] EXAONE 모델 사전 로딩 완료. AI 질문 생성 준비됨.")
    except Exception as e:
        logger.warning(f"⚠️ [Preload] 모델 사전 로딩 실패 (AI 질문 생성 시 자동 재시도): {e}")


@shared_task(bind=True, name="tasks.question_generation.generate_next_question")
def generate_next_question_task(self, interview_id: int):
    """
    인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    """
    from db import engine, Session, select, Interview, Transcript, Speaker, Question, save_generated_question
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
            # 4. [최적화] template stage는 RAG/LLM 없이 즉시 포맷
            if next_stage.get("type") == "template":
                candidate_name = "지원자"
                target_role = interview.position or "해당 직무"
                cert_list = ""
                
                act_org, act_role = "관련 기관", "담당 업무"
                proj_org, proj_name = "해당 기관", "수행한 프로젝트"
                
                if interview.resume and interview.resume.structured_data:
                    sd = interview.resume.structured_data
                    if isinstance(sd, str): sd = json.loads(sd)
                    
                    header = sd.get("header", {})
                    candidate_name = header.get("name") or header.get("candidate_name") or candidate_name
                    target_role = header.get("target_role") or target_role
                    company_name = header.get("target_company") or header.get("company") or "저희 회사"

                    # 1. 자격증 리스트업 (모두 추출)
                    certs = sd.get("certifications", [])
                    if certs:
                        cert_names = [c.get("title") or c.get("name") for c in certs if (c.get("title") or c.get("name"))]
                        cert_list = ", ".join(cert_names)
                    
                    # 4-1. 경력 (activities) - 헤더 제외 로직
                    acts = sd.get("activities", [])
                    act_header_kws = ["기간", "역할", "기관", "소속", "장소", "제목", "내용"]
                    for act in acts:
                        tmp_org = act.get("organization") or act.get("name") or ""
                        tmp_role = act.get("role") or act.get("position") or ""
                        if not any(kw in tmp_org for kw in act_header_kws) and not any(kw in tmp_role for kw in act_header_kws):
                            act_org = tmp_org or act_org
                            act_role = tmp_role or act_role
                            break
                    
                    # 4-2. 프로젝트 (projects) - 헤더 제외 로직
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
                    "company_name": company_name if 'company_name' in locals() else "저희 회사",
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
                    # 폴백: 직접 문자열 치환
                    for k, v in template_vars.items():
                        tpl = tpl.replace("{" + k + "}", str(v))
                    formatted = tpl

                intro_msg = next_stage.get("intro_sentence", "")
                display_name = next_stage.get("display_name", "면접질문")
                final_content = f"[{display_name}] {intro_msg} {formatted}".strip() if intro_msg else f"[{display_name}] {formatted}"
                logger.info(f"Template stage '{next_stage['stage']}' (v2) → 즉시 포맷 완료 (Direct Extraction)")

            elif next_stage.get("type") == "template_quoted":
                # ==========================================
                # [template_quoted] RAG 문장 추출 후 template 직접 주입 (hallucination 차단)
                # ==========================================
                query_template_tq = next_stage.get("query_template", interview.position)
                try:
                    query_tq = query_template_tq.format(
                        target_role=interview.position or "해당 직무",
                        major=major or ""
                    )
                except (KeyError, ValueError):
                    query_tq = query_template_tq

                rag_results_tq = retrieve_context(query_tq, resume_id=interview.resume_id, top_k=5)
                raw_text = "\n".join([r['text'] for r in rag_results_tq]) if rag_results_tq else ""

                # 텍스트 정규화: 개행을 공백으로 변환
                normalized_text = re.sub(r'\n+', ' ', raw_text).strip()

                # 한국어 문장 단위 분리 (하다. / 입니다. / 거니다. 등)
                sentences = re.split(r'(?<=[\ub2e4\uc694])\. ?', normalized_text)

                extract_keywords = next_stage.get("extract_keywords", [])
                quote = ""

                if extract_keywords and sentences:
                    best_sentence = ""
                    best_score = 0
                    for sent in sentences:
                        sent = sent.strip()
                        if len(sent) < 10:
                            continue
                        score = sum(1 for kw in extract_keywords if kw in sent)
                        if score > best_score or (score == best_score and len(sent) > len(best_sentence)):
                            best_score = score
                            best_sentence = sent
                    if best_sentence and best_score > 0:
                        # 문장 끝 마침표 복원
                        quote = best_sentence.rstrip('.') + '.'

                # 폴백: 키워드 매칭 실패 시 첫 번째 의미있는 문장 사용
                if not quote:
                    fallback_sents = [s.strip() for s in sentences if len(s.strip()) > 20]
                    quote = fallback_sents[0].rstrip('.') + '.' if fallback_sents else "자기소개서에 기재하신 내용"

                # template 변수 준비
                candidate_name_tq = "지원자"
                target_role_tq = interview.position or "해당 직무"
                if interview.resume and interview.resume.structured_data:
                    sd_tq = interview.resume.structured_data
                    if isinstance(sd_tq, str): sd_tq = json.loads(sd_tq)
                    candidate_name_tq = sd_tq.get("header", {}).get("name", "지원자")

                tpl_tq = next_stage.get("template", "{candidate_name} 지원자님, 자기소개서에 '{quote}'라고 쓰셨는데, 이에 대해 구체적으로 말씀해 주세요.")
                try:
                    formatted = tpl_tq.format(
                        candidate_name=candidate_name_tq,
                        quote=quote,
                        target_role=target_role_tq
                    )
                except Exception as fmt_err:
                    logger.warning(f"template_quoted formatting error: {fmt_err}")
                    formatted = tpl_tq.replace("{candidate_name}", candidate_name_tq).replace("{quote}", quote).replace("{target_role}", target_role_tq)

                display_name = next_stage.get("display_name", "면접질문")
                intro_msg = next_stage.get("intro_sentence", "")
                final_content = f"[{display_name}] {intro_msg} {formatted}".strip() if intro_msg else f"[{display_name}] {formatted}"
                logger.info(f"template_quoted stage '{next_stage['stage']}' → 인용문 추출 성공: '{quote[:60]}...'")

            else:
                # [로직 단순환] 꼬리질문과 일반 질문의 컨텍스트 분리
                if next_stage.get("type") == "followup":
                    # 꼬리질문: RAG/질문은행 모두 스킵하고 오직 '질문-답변' 맥락만 사용 (환각 0%)
                    logger.info("🎯 Follow-up mode: RAG & Question Bank disabled. Focusing purely on conversation context.")
                    context_text = f"이전 질문: {last_ai_transcript.text if last_ai_transcript else '없음'}\n"
                    if last_user_transcript:
                        context_text += f"[지원자의 최근 답변]: {last_user_transcript.text}"
                    rag_results = []
                else:
                    # 일반 AI 질문 (경험/문제해결 등): 이력서 RAG 검색 수행
                    query_template = next_stage.get("query_template", interview.position)
                    try:
                        query = query_template.format(
                            target_role=interview.position or "해당 직무",
                            major=major or ""
                        )
                    except (KeyError, ValueError):
                        query = query_template

                    category_raw = next_stage.get("category")
                    rag_results = []
                    context_text = ""

                    if category_raw == "certification" and interview.resume and interview.resume.structured_data:
                        sd = interview.resume.structured_data
                        if isinstance(sd, str): sd = json.loads(sd)
                        certs = sd.get("certifications", [])
                        important_certs = [c for c in certs if any(kw in c.get('title', '') for kw in ["데이터", "분석", "RAG", "AI", "클라우드", "SQL", "ADSP", "정보처리"])]
                        final_certs = important_certs if important_certs else certs
                        if final_certs:
                            logger.info(f"✅ RAG 건너뜀 (구조화 데이터 활용)")
                            context_text = "지원자가 보유한 자격증 목록:\n" + "\n".join([f"- {c.get('title')}" for c in final_certs])
                            rag_results = [{'text': f"자격명: {final_certs[0].get('title')}"}]
                        else:
                            rag_results = retrieve_context(query, resume_id=interview.resume_id, top_k=3)
                            context_text = "\n".join([r['text'] for r in rag_results]) if rag_results else "특별한 정보 없음"
                    else:
                        filter_type = None
                        if category_raw == "certification": filter_type = "certifications"
                        rag_results = retrieve_context(query, resume_id=interview.resume_id, top_k=3, filter_type=filter_type)
                        context_text = "\n".join([r['text'] for r in rag_results]) if rag_results else "특별한 정보 없음"
                        
                    if last_user_transcript:
                        context_text += f"\n[지원자의 최근 답변]: {last_user_transcript.text}"

                llm = get_exaone_llm()
                prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt | llm | StrOutputParser()

                # Redis 설정 (스트리밍 전송용)
                redis_host = os.getenv("REDIS_HOST", "redis")
                r = redis.Redis(host=redis_host, port=6379, db=0)
                channel = f"interview_{interview_id}_stream"

                logger.info(f"🚀 Starting streaming generation for Interview {interview_id}")
                
                full_tokens = []
                # stream()을 사용하여 토큰 단위로 실시간 수신
                for chunk in chain.stream({
                    "context": context_text,
                    "stage_name": next_stage['display_name'],
                    "guide": next_stage.get('guide', ''),
                    "target_role": interview.position or "지원 직무"
                }):
                    if chunk:
                        full_tokens.append(chunk)
                        # Redis Pub/Sub으로 토큰 발행 (실시간 스트리밍)
                        try:
                            r.publish(channel, chunk)
                        except Exception as pub_err:
                            logger.error(f"Redis publish failed: {pub_err}")

                final_content = "".join(full_tokens)

                # [추가] AI 응답 정제: 따옴표, 숫자, '질문:' 등 불필요한 장식 제거
                final_content = final_content.strip()
                # 1. 앞뒤 따옴표 제거
                final_content = re.sub(r'^["\'\s]+|["\'\s]+$', '', final_content)
                # 2. 앞줄 번호나 '질문:' 등의 태그 제거 (예: '1.', '질문:', "'1.")
                final_content = re.sub(r'^(\'?\d+\.|\'?질문:|\'?Q:|\'?-\s*)\s*', '', final_content)
                # 3. 중복 공백 제거 및 다시 한번 다듬기
                final_content = final_content.strip()

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
                    intro_msg = "" # 프롬프트에서 이미 생성하므로 중복 방지를 위해 비움
                
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
                rubric_json=next_stage.get('rubric'),  # stage별 루브릭 주입
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