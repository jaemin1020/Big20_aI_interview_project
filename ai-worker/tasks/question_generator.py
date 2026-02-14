import sys
import os
import time
import gc 
import logging
import torch
from datetime import datetime
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# AI-Worker 루트 디렉토리를 찾아 sys.path에 추가
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# -----------------------------------------------------------
# [1. 모델 및 경로 설정]
# -----------------------------------------------------------
local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

if os.path.exists(local_path):
    model_path = local_path
else:
    model_path = docker_path

# 🚨 DB 조회를 위해 추가
try:
    from db import engine
    from sqlalchemy import text as sql_text
except ImportError:
    engine = None


# 🚨 ExaoneLLM은 함수 내부에서 import (Celery 로딩 시점 문제 회피)

# -----------------------------------------------------------
# [2. 프롬프트 템플릿]
# -----------------------------------------------------------
PROMPT_TEMPLATE = """[|system|]
너는 대한민국 최고의 기술 기업에서 신입 및 경력 사원을 선발하는 최고의 {position} 전문 면접관이다.
지원자의 이력서(RAG)와 이전 대화 내용을 완벽히 파악하여, 해당 지원자에게만 던질 수 있는 **'초개인화(Hyper-Personalization)'** 질문을 생성하라.

[작성 지침 - 절대 규칙]
1. **단 두 문장, 150자 이내**: 모든 질문은 반드시 **최대 두 문장(150자 이내)**으로 생성하라.
2. **맥락별 인용 우선순위**: 
   - 일반 질문: [이력서 내용] 인용 + 질문
   - 꼬리 질문(followup): **[지원자의 최근 답변]** 속 핵심 키워드(기술명, 수치, 조치 사항 등)를 반드시 인용 + 그에 대한 적절한 수준의 구체적 확인 질문
3. **사족 금지**: "답변 잘 들었습니다" 등의 추임새는 0점 처리한다. 바로 인용문으로 시작하라.
4. **실무형 난이도**: 너무 난해하거나 학술적인 질문 대신, 실무 단계에서 겪을 법한 **'구체적인 상황'이나 '본인의 역할'**에 대해 물어보라.
[|endofturn|]
[|user|]
# 평가 단계: {stage}
# 평가 의도: {guide}
# 지원자 고유 정보 및 근거 (RAG + 대화 로그):
{context}

# 요청:
지원자 {name}님의 이력서와 발언을 바탕으로, 그의 실무 역량을 편안하게 검증할 수 있는 **구체적인** 질문 1개만 생성해줘.
[|endofturn|]
[|assistant|]
"""

# -----------------------------------------------------------
# [3. 질문 생성 핵심 함수]
# -----------------------------------------------------------
# -----------------------------------------------------------
# [3. 질문 생성 핵심 함수]
# [기존 일괄 생성 태스크 삭제됨 - 실시간 생성 모드로 통합]

# -----------------------------------------------------------
# [5. Celery Task] - 실시간 1개씩 생성하는 태스크 (수정 완료)
# -----------------------------------------------------------
@shared_task(name="tasks.question_generation.generate_next_question")
def generate_next_question_task(interview_id: int):
    logger.info(f"🔥 [START] generate_next_question_task for Interview {interview_id}")
    
    from db import (
        engine, Session, select, save_generated_question,
        Interview, Transcript, Speaker, Question, Resume

    )
    from config.interview_scenario import get_stage_by_name, get_next_stage
    from utils.exaone_llm import get_exaone_llm
    
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if not interview: 
            logger.error(f"Interview {interview_id} not found.")
            return {"status": "error", "message": "Interview not found"}
            
        # 🚨 [Race Condition 방지] 중복 생성 체크
        # 마지막 AI 발화 이후에 사용자 답변이 아직 없는 상태에서, 
        # 마지막 AI 발화가 너무 최근(10초 이내)이면 중복 생성 요청으로 간주
        stmt_check = select(Transcript).where(
            Transcript.interview_id == interview_id
        ).order_by(Transcript.id.desc())
        last_transcript = session.exec(stmt_check).first()
        
        if last_transcript and last_transcript.speaker == Speaker.AI:
            diff = (datetime.utcnow() - last_transcript.timestamp).total_seconds()
            if diff < 10: # AI가 방금 말했는데 또 말하라고 하면 스킵
                logger.warning(f"⚠️ [SKIP] AI just spoke {diff:.1f}s ago. Waiting for user response.")
                return {"status": "skipped", "reason": "ai_just_spoke"}


        # 🔍 현재 단계(Stage) 판별 로직 고도화
        # 1. 마지막으로 '사용자가 답변한' 질문을 찾음 (가장 정확한 지표)
        # Transcript의 order 필드를 기준으로 정렬하여 시나리오 순서 보장
        stmt_user = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker == Speaker.USER
        ).order_by(Transcript.order.desc(), Transcript.id.desc())
        last_user_transcript = session.exec(stmt_user).first()
        
        last_stage_name = None
        if last_user_transcript and last_user_transcript.question_id:
            last_q = session.get(Question, last_user_transcript.question_id)
            if last_q:
                last_stage_name = last_q.question_type
                logger.info(f"Detected Last Answered Stage: {last_stage_name}")

        # 2. 만약 사용자 답변이 없으면 (면접 극초기), 마지막 AI 질문을 참고
        if not last_stage_name:
            stmt_ai = select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == Speaker.AI
            ).order_by(Transcript.id.desc())
            last_ai_transcript = session.exec(stmt_ai).first()
            if last_ai_transcript and last_ai_transcript.question_id:
                last_q = session.get(Question, last_ai_transcript.question_id)
                if last_q:
                    # AI가 질문만 내뱉고 답변을 안 한 상태이므로, 
                    # 한 단계 뒤로 물러나서 판단하거나 현재 상태를 유지
                    ai_stage = last_q.question_type
                    
                    # 'intro'나 'motivation'은 API에서 미리 두 개를 생성하므로 특별 처리
                    if ai_stage == "motivation":
                        # 아직 사용자가 동기를 말 안 했으면 intro까지만 끝난 것으로 간주 가능 (상황에 따라)
                        # 여기서는 보수적으로 AI가 보낸 마지막 단계 전 단계를 탐색
                        last_stage_name = "intro" 
                    else:
                        last_stage_name = ai_stage
                logger.info(f"Detected Last AI-Spoken Stage (Used as Fallback): {last_stage_name}")
        
        # 🚨 [Legacy/Alias 보정] DB에 저장된 예전 명칭들을 최신 시나리오 명칭으로 통일
        mapping_fix = {
            "technical": "skill",
            "personality": "communication",
            "values": "responsibility"
        }
        if last_stage_name in mapping_fix:
            logger.info(f"Applying legacy mapping fix: {last_stage_name} -> {mapping_fix[last_stage_name]}")
            last_stage_name = mapping_fix[last_stage_name]

        # 🔍 다음 단계 결정
        if not last_stage_name:
            # 아예 기록이 없으면 intro부터 시작 (보통 interviews.py에서 생성하므로 여기선 motivation이 될 가능성이 높음)
            next_stage_data = get_stage_by_name("intro")
        else:
            next_stage_data = get_next_stage(last_stage_name)

        if not next_stage_data:
            logger.info(f"🏁 Scenario Completed for Interview {interview_id}. Updating status to COMPLETED.")
            try:
                interview.status = "COMPLETED" # InterviewStatus.COMPLETED
                interview.end_time = datetime.utcnow()
                session.add(interview)
                session.commit()
                
                # 리포트 생성 태스크 즉시 트리거
                from tasks.evaluator import generate_final_report
                generate_final_report.apply_async(args=[interview_id])
                logger.info(f"📊 Triggered final report generation for Interview {interview_id}")
            except Exception as e:
                logger.error(f"Failed to update interview status to COMPLETED: {e}")
                
            return {"status": "completed"}

        stage_name = next_stage_data["stage"]

        # 🚨 [중복 생성 절대 방지] 해당 단계가 이미 존재하는지 체크
        stmt_exist = select(Transcript).join(Question).where(
            Transcript.interview_id == interview_id,
            Question.question_type == stage_name
        )
        existing_q = session.exec(stmt_exist).first()
        if existing_q:
            logger.warning(f"⚠️ [SKIP] Stage '{stage_name}' already exists for Interview {interview_id}. No need to generate.")
            return {"status": "already_exists", "stage": stage_name}
        
        logger.info(f"Final Target Stage to Generate: {stage_name}")
        stage_type = next_stage_data.get("type", "ai")
        
        if stage_type == "template" or stage_type == "final":
            from utils.interview_helpers import get_candidate_info
            from db import Resume
            resume = session.get(Resume, interview.resume_id)
            c_info = get_candidate_info(resume.structured_data if resume else {})
            tmpl = next_stage_data.get("template", "{candidate_name}님, 다음 질문입니다.")
            content = tmpl.format(candidate_name=c_info.get("candidate_name", "지원자"), target_role=interview.position)
            
            # QuestionCategory Enum에 'general'이 없으므로 'behavioral' 사용
            save_generated_question(interview_id, content, "behavioral", stage_name, "")
            return {"status": "success", "stage": stage_name}

        # [LangChain LCEL] AI 생성 파이프라인
        try:
            # 1. 모델 및 파서 준비
            llm = get_exaone_llm()
            output_parser = StrOutputParser()
            
            # 2. 컨텍스트 및 프롬프트 구성
            from .rag_retrieval import get_retriever
            
            # [수정] 꼬리질문이든 일반 질문이든 기본적으로 이력서(RAG) 베이스라인을 가져옴
            query_tmpl = next_stage_data.get("query_template", "{target_role}")
            if stage_type == "followup" and not next_stage_data.get("query_template"):
                parent_stage_name = next_stage_data.get("parent")
                parent_data = get_stage_by_name(parent_stage_name) if parent_stage_name else None
                query = parent_data.get("query_template", "{target_role}").format(target_role=interview.position) if parent_data else interview.position
            else:
                query = query_tmpl.format(target_role=interview.position)

            # [수정] 꼬리질문 및 초개인화를 위한 컨텍스트 구성
            resume = session.get(Resume, interview.resume_id)
            profile_summary = ""
            narrative_context = ""
            
            if resume and resume.structured_data:
                sd = resume.structured_data
                header = sd.get("header", {})
                education = sd.get("education", [])
                edu_info = ""
                if education:
                    latest_edu = education[0]
                    school = latest_edu.get("school", "")
                    major = latest_edu.get("major", "")
                    if school or major:
                        edu_info = f"학력: {school} ({major})"
                
                skills = ", ".join(sd.get("skills", [])[:5])
                profile_summary = f"[지원자 기본 정보]\n- 성함: {header.get('name', '지원자')}\n- 지원 직무: {interview.position}\n- {edu_info}\n- 주요 기술: {skills}\n\n"

                # [추가] 특정 단계별 자기소개서 특정 문항 정밀 매핑
                if stage_name == "communication":
                    self_intro = sd.get("self_intro", [])
                    q3_data = next((item for item in self_intro if "[질문3]" in item.get("question", "")), None)
                    if not q3_data and len(self_intro) >= 3: q3_data = self_intro[2]
                    if q3_data:
                        narrative_context = f"[자기소개서 3번 내용 - 협업]\n질문: {q3_data.get('question')}\n답변: {q3_data.get('answer')}\n\n"

                elif stage_name == "responsibility":
                    self_intro = sd.get("self_intro", [])
                    q1_data = next((item for item in self_intro if "[질문1]" in item.get("question", "")), None)
                    if not q1_data and len(self_intro) >= 1: q1_data = self_intro[0]
                    if q1_data:
                        narrative_context = f"[자기소개서 1번 내용 - 가치관]\n질문: {q1_data.get('question')}\n답변: {q1_data.get('answer')}\n\n"

                elif stage_name == "growth":
                    self_intro = sd.get("self_intro", [])
                    q2_data = next((item for item in self_intro if "[질문2]" in item.get("question", "")), None)
                    if not q2_data and len(self_intro) >= 2: q2_data = self_intro[1]
                    if q2_data:
                        narrative_context = f"[자기소개서 2번 내용 - 성장의지]\n질문: {q2_data.get('question')}\n답변: {q2_data.get('answer')}\n\n"

            # Retriever 기반 컨텍스트 검색
            retriever = get_retriever(resume_id=interview.resume_id, top_k=5)
            retrieved_docs = retriever.invoke(query)
            rag_context = "\n".join([f"- {doc.page_content}" for doc in retrieved_docs]) if retrieved_docs else "이력서 세부 근거 없음"

            # [핵심 로직] 2. 프로필 + 이력서(RAG) + '방금 한 답변'을 섞어서 LLM에게 전달
            if stage_type == "followup":
                # 꼬리질문: 프로필 + RAG + 이전 답변 결합
                user_stmt = select(Transcript).where(
                    Transcript.interview_id == interview_id,
                    Transcript.speaker == Speaker.USER
                ).order_by(Transcript.id.desc())
                last_user_ans = session.exec(user_stmt).first()
                user_ans_text = last_user_ans.text if last_user_ans else "이전 답변 없음"
                
                context_text = f"{profile_summary}{narrative_context}[이력서 세부 내용]\n{rag_context}\n\n[지원자의 최근 답변]\n{user_ans_text}"
            else:
                # 일반 AI 질문: 프로필 + RAG 결합
                context_text = f"{profile_summary}{narrative_context}[이력서 세부 내용]\n{rag_context}"

            # 3. 지원자 정보 정제
            resume = session.get(Resume, interview.resume_id)
            candidate_name = "지원자"
            target_role = interview.position
            if resume and resume.structured_data:
                header = resume.structured_data.get("header", {})
                candidate_name = header.get("name") or header.get("candidate_name") or candidate_name
                target_role = header.get("target_role") or target_role

            # 4. LCEL 체인 정의 및 실행 (Prompt | LLM | Parser)
            prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)

            chain = prompt | llm | output_parser

            
            logger.info(f"🔗 Executing LCEL Chain for stage: {stage_name}")
            content = chain.invoke({
                "position": target_role,
                "name": candidate_name,
                "stage": stage_name,
                "guide": next_stage_data.get("guide", "역량을 확인하기 위한 질문을 해주세요."),
                "context": context_text
            })
            
            if not content:
                content = f"{candidate_name}님, 준비하신 내용을 토대로 해당 역량에 대해 더 말씀해주실 수 있나요?"
            
            # 5. 결과 저장
            category_raw = next_stage_data.get("category", "technical")
            category_map = {"certification": "technical", "project": "technical", "narrative": "behavioral", "problem_solving": "situational"}
            db_category = category_map.get(category_raw, "technical")
            
            logger.info(f"💾 Saving generated question to DB for Interview {interview_id} (Stage: {stage_name})")
            save_generated_question(interview_id, content, db_category, stage_name, next_stage_data.get("guide", ""), session=session)
            return {"status": "success", "stage": stage_name, "question": content}
        except Exception as e:
            logger.error(f"실시간 질문 생성 실패: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            gc.collect()