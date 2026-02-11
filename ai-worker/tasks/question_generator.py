import sys
import os
import time
import gc 
import logging
import torch
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager
from langchain_core.prompts import PromptTemplate

# AI-Worker 루트 디렉토리를 찾아 sys.path에 추가
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# -----------------------------------------------------------
# [1. 모델 및 경로 설정]
# -----------------------------------------------------------
local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

model_path = local_path if os.path.exists(local_path) else docker_path

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
너는 15년 차 베테랑 {position} 전문 면접관이다. 
지금은 **면접이 한창 진행 중인 상황**이다. (자기소개는 이미 끝났다.)
제공된 [지원자 이력서 근거] 데이터를 바탕으로, 해당 단계({stage})에 맞는 **핵심적인 질문 1개**만 던져라.

[작성 절대 금지 사항] 
1. **"자기소개 부탁드립니다" 절대 금지.**
2. **"(잠시 침묵)", "답변 감사합니다"** 같은 대본용 지문을 쓰지 마라.
3. **[프로젝트], [회사 명]** 같은 자리표시자(Placeholder)를 그대로 노출하지 말고, 근거 데이터에 있는 실제 명칭을 써라.
4. 질문 앞뒤에 사족을 붙이지 말고 **질문만 딱 한 문장(최대 두 문장)**으로 출력하라.

[질문 스타일 가이드]
1. 시작은 반드시 **"{name}님,"** 으로 부르며 시작할 것.
2. 질문이 너무 길어지지 않게 핵심만 명확히 물어볼 것. 꼬아내지 말고 정공법으로 물어볼 것.
3. 말투는 정중하게(..하셨나요?, ..부탁드립니다.) 유지할 것.
[|endofturn|]
[|user|]
# 평가 단계: {stage}
# 평가 의도: {guide}
# 지원자 이력서 근거 (RAG):
{context}

# 요청:
위의 근거 데이터를 기반으로 {name} 지원자에게 **구체적이고 단도직입적인** 질문을 던져줘.
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
            
        # 🔍 마지막 단계 탐지 최적화 (순서 기반이 아닌 ID 기반 최신 데이터 조회)
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker == Speaker.AI
        ).order_by(Transcript.id.desc()) # ID가 가장 큰 것이 절대적으로 최신
        last_ai_transcript = session.exec(stmt).first()
        
        last_stage_name = None
        if last_ai_transcript:
            if last_ai_transcript.question_id:
                last_q = session.get(Question, last_ai_transcript.question_id)
                if last_q:
                    # 1순위: DB에 저장된 타입 정보 사용
                    last_stage_name = last_q.question_type
                    
                    # 2순위 (Fallback): 저장된 타입이 없으면 텍스트 내용으로 유추
                    if not last_stage_name:
                        content = last_q.content
                        if "자기소개" in content: last_stage_name = "intro"
                        elif "지원 동기" in content or "지원하게 된" in content: last_stage_name = "motivation"
                        elif "기술" in content or "스킬" in content or "도구" in content: last_stage_name = "skill"
                        elif "프로젝트" in content or "경험" in content: last_stage_name = "experience"
                        elif "어려움" in content or "해결" in content: last_stage_name = "problem_solving"
            
            # 3순위: transcript의 order를 기반으로 역추적 (scenario의 order와 매칭)
            if not last_stage_name and last_ai_transcript.order is not None:
                from config.interview_scenario import INTERVIEW_STAGES
                # transcript.order는 0부터 시작, scenario order는 1부터 시작할 수 있으므로 보정 필요
                # 여기서는 scenario의 order 필드를 검색
                for s in INTERVIEW_STAGES:
                    if s["order"] == last_ai_transcript.order + 1:
                        last_stage_name = s["stage"]
                        break

        # 4순위: 매핑 보정 (Legacy 데이터 등)
        if last_stage_name == "technical": last_stage_name = "skill"
        
        if not last_stage_name:
            last_stage_name = "intro"

        logger.info(f"Detected Last Stage: {last_stage_name}")
        
        next_stage_data = get_next_stage(last_stage_name)
        if not next_stage_data:
            logger.info("Scenario Completed.")
            return {"status": "completed"}
            
        stage_name = next_stage_data["stage"]
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

        # AI 생성 루틴
        try:
            exaone = get_exaone_llm()
            
            # 컨텍스트 준비: 꼬리질문 vs 일반 AI 질문 명확히 분리
            contexts = []
            if stage_type == "followup":
                # 꼬리질문: 오직 이전 답변만 사용 (RAG 검색 안 함)
                user_stmt = select(Transcript).where(
                    Transcript.interview_id == interview_id,
                    Transcript.speaker == Speaker.USER # Enum 값이 "User"이므로 일치함
                ).order_by(Transcript.id.desc())
                last_user_ans = session.exec(user_stmt).first()
                if last_user_ans:
                    contexts = [{"text": f"이전 답변: {last_user_ans.text}", "meta": {"category": "followup"}}]
                    logger.info(f"📌 Follow-up context prepared from last answer.")
                else:
                    logger.warning("⚠️ No previous answer found for followup question!")
                    contexts = [{"text": "이전 답변을 찾을 수 없습니다.", "meta": {}}]
            else:
                # 일반 AI 질문: 이력서 RAG 검색
                from .rag_retrieval import retrieve_context
                query_tmpl = next_stage_data.get("query_template", "{target_role}")
                query = query_tmpl.format(target_role=interview.position)
                contexts = retrieve_context(query, resume_id=interview.resume_id, top_k=3)

            
            # 지원자 정보 및 직무 정보 가져오기 보강 (JSON header/metadata 우선)
            resume = session.get(Resume, interview.resume_id)
            candidate_name = "지원자"
            target_role = interview.position # 기본값 (인터뷰 세션 설정값)
            
            if resume and resume.structured_data:
                s_data = resume.structured_data
                header_data = s_data.get("header", {})
                
                # 1. 이름 추출 (header -> User 테이블 순)
                candidate_name = header_data.get("name") or header_data.get("candidate_name")
                if not candidate_name and resume.candidate_id:
                    from db import User
                    user = session.get(User, resume.candidate_id)
                    if user: candidate_name = user.full_name or user.username
                
                # 2. 직무 추출 (header에 있으면 최우선)
                target_role = header_data.get("target_role") or target_role

            logger.info(f"Target Candidate Name: {candidate_name}, Role: {target_role}")
            
            # 1. 컨텍스트 텍스트 조립
            context_text = "\n".join([f"- {c['text']}" for c in contexts]) if contexts else "이력서 근거 부족"
            
            # 2. PROMPT_TEMPLATE을 사용하여 최종 프롬프트 생성 (사용자 요청 반영)
            full_prompt = PROMPT_TEMPLATE.format(
                position=target_role,
                name=candidate_name,
                stage=stage_name,
                guide=next_stage_data.get("guide", "역량을 확인하기 위한 질문을 해주세요."),
                context=context_text
            )
            
            logger.info(f"Generated Full Prompt length: {len(full_prompt)}")
            
            # 3. AI 질문 생성 실행 (엔진에게는 생성만 위임)
            content = exaone.invoke(full_prompt, max_tokens=256, temperature=0.6)
            
            if not content:
                content = f"{candidate_name}님, 준비하신 내용을 토대로 해당 역량에 대해 더 말씀해주실 수 있나요?"
            
            # 시나리오의 카테고리를 DB Enum에 맞게 매핑
            category_raw = next_stage_data.get("category", "technical")
            category_map = {
                "certification": "technical",
                "project": "technical",
                "narrative": "behavioral",
                "problem_solving": "situational"
            }
            db_category = category_map.get(category_raw, "technical")
            
            save_generated_question(interview_id, content, db_category, stage_name, next_stage_data.get("guide", ""))
            return {"status": "success", "stage": stage_name, "question": content}
        except Exception as e:
            logger.error(f"실시간 질문 생성 실패: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            gc.collect()
