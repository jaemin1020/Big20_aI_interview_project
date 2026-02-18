import sys
import os
import re
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
2. **평가 의도(Guide) 중심**: 지원자 정보(RAG)보다 현재 평가 단계의 **'평가 의도({guide})'**를 80% 비중으로 우선하여 질문을 구성하라.
3. **직무 지식(skill) 단계 특화**: 만약 현재 단계가 'skill'이라면, 이력서의 기술 키워드를 1개 인용하여 실무 개념을 묻는 **쉬운(Easy) 난이도**의 질문을 하라.
4. **꼬리 질문(followup) 규칙**: 반드시 지원자의 최근 답변 내용을 **한 문장으로 짧게 요약("~라고 말씀해 주셨는데,")**한 뒤, 그와 연관된 심층 질문을 던져라. "답변 잘 들었습니다" 같은 말은 절대 하지 마라.
5. **출처 명시**: 질문 시작 시 반드시 근거가 되는 출처(예: "이력서 내 경력사항을 보니", "자기소개서 2번 문항을 보니")를 언급하라.
6. **가독성 및 금지사항**: 강조 기호(**)나 특수 문자를 사용하지 말고, 순수 텍스트로만 답변하라. 질문 외의 사족은 일절 배제하라.
[|endofturn|]
[|user|]
# 평가 단계: {stage}
# 시나리오 가이드: {guide}
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
    from utils.exaone_llm import get_exaone_llm
    
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if not interview: 
            logger.error(f"Interview {interview_id} not found.")
            return {"status": "error", "message": "Interview not found"}

        # [추가] 직무 전환 여부 확인 및 시나리오 분기
        resume = session.get(Resume, interview.resume_id)
        major = ""
        if resume and resume.structured_data:
            education = resume.structured_data.get("education", [])
            if education and isinstance(education, list) and len(education) > 0:
                major = education[0].get("major", "")
        
        # transition 여부 판별 (백엔드와 동일한 키워드 기준)
        is_transition = False
        target_role = interview.position or ""
        if major and target_role:
            tech_role_keywords = ['개발', '엔지니어', '프로그래머', 'IT', 'SW', '소프트웨어', '데이터', '인공지능', 'AI', '보안', '시스템']
            tech_major_keywords = ['컴퓨터', '소프트웨어', '정보통신', '전기', '전자', 'IT', '데이터', '인공지능', 'AI', '수학', '통계', '산업공학']
            is_tech_role = any(kw in target_role for kw in tech_role_keywords)
            is_tech_major = any(kw in major for kw in tech_major_keywords)
            if is_tech_role and not is_tech_major:
                is_transition = True
        
        # 시나리오 모듈 선택적 임포트
        if is_transition:
            from config.interview_scenario_transition import get_stage_by_name, get_next_stage
            logger.info(f"✨ [AI-WORKER] Transition scenario selected (Major: {major})")
        else:
            from config.interview_scenario import get_stage_by_name, get_next_stage
            logger.info("✅ [AI-WORKER] Standard scenario selected")
            
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
                        narrative_context = f"[자기소개서 질문 3번 내용 - 협업]\n답변 내용: {q3_data.get('answer')}\n\n"

                elif stage_name == "responsibility":
                    self_intro = sd.get("self_intro", [])
                    q1_data = next((item for item in self_intro if "[질문1]" in item.get("question", "")), None)
                    if not q1_data and len(self_intro) >= 1: q1_data = self_intro[0]
                    if q1_data:
                        narrative_context = f"[자기소개서 질문 1번 내용 - 가치관]\n답변 내용: {q1_data.get('answer')}\n\n"

                elif stage_name == "growth":
                    self_intro = sd.get("self_intro", [])
                    q2_data = next((item for item in self_intro if "[질문2]" in item.get("question", "")), None)
                    if not q2_data and len(self_intro) >= 2: q2_data = self_intro[1]
                    if q2_data:
                        narrative_context = f"[자기소개서 질문 2번 내용 - 성장의지]\n답변 내용: {q2_data.get('answer')}\n\n"

            # Retriever 기반 컨텍스트 검색
            retriever = get_retriever(resume_id=interview.resume_id, top_k=10)
            retrieved_docs = retriever.invoke(query)
            
            # [수정] 카테고리 정보를 포함하여 지식의 성격(경험 vs 계획)을 명시
            rag_context_list = []
            if retrieved_docs:
                for doc in retrieved_docs:
                    cat = doc.metadata.get('category', 'unknown')
                    # 카테고리명을 더 직관적으로 변환하여 LLM에 전달
                    cat_name = "경험/활동" if cat in ['project', 'experience', 'activity', 'award'] else "자기소개/계획"
                    rag_context_list.append(f"- [{cat_name}] {doc.page_content}")
                rag_context = "\n".join(rag_context_list)
            else:
                rag_context = "이력서 세부 근거 없음"

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

            # [추가] 실시간 디버깅 및 사용자 확인을 위한 로그 출력
            logger.info("========================================")
            logger.info(f"🔍 [LLM INPUT CONTEXT] (Interview ID: {interview_id}, Stage: {stage_name})")
            logger.info(context_text)
            logger.info("========================================")

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
                "context": context_text,
                "position": interview.position,
                "stage": stage_name,
                "guide": next_stage_data.get("guide", ""),
                "name": candidate_name
            })
            
            # [수정] 강조 기호(**) 및 마크다운 제거
            content = re.sub(r'\*\*|__', '', content)
            # 단일 문장 내의 불필요한 공백 및 개행 정리
            content = " ".join(content.split())
            
            if not content:
                content = f"{candidate_name}님, 준비하신 내용을 토대로 해당 역량에 대해 더 말씀해주실 수 있나요?"
            
            # 5. 결과 저장
            category_raw = next_stage_data.get("category", "technical")
            category_map = {"certification": "technical", "project": "technical", "narrative": "behavioral", "problem_solving": "situational"}
            db_category = category_map.get(category_raw, "technical")
            
            # [추가] 면접 단계별 한국어 명칭 및 안내 문구 가져오기
            from config.interview_scenario import INTERVIEW_STAGES
            stage_display = "심층 면접"
            intro_msg = ""
            for s in INTERVIEW_STAGES:
                if s["stage"] == stage_name:
                    stage_display = s.get("display_name", stage_display)
                    intro_msg = s.get("intro_sentence", "")
                    break
            
            # 꼬리질문의 경우 고정된 인트로 추가 (중복 방지를 위해 LLM에게는 시키지 않음)
            if stage_type == "followup":
                intro_msg = "추가적으로 궁금한 점이 있습니다."
            elif intro_msg == "추가적으로 궁금한 점이 있습니다.":
                # 메인 질문인데 시나리오에 잘못 들어가 있는 경우 제거
                intro_msg = ""

            # 질문 앞에 [단계] 및 안내 문구 추가
            final_content = f"[{stage_display}] {intro_msg} {content}" if intro_msg else f"[{stage_display}] {content}"
            
            logger.info(f"💾 Saving generated question to DB for Interview {interview_id} (Stage: {stage_name})")
            save_generated_question(interview_id, final_content, db_category, stage_name, next_stage_data.get("guide", ""), session=session)
            return {"status": "success", "stage": stage_name, "question": final_content}
        except Exception as e:
            logger.error(f"실시간 질문 생성 실패: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            gc.collect()