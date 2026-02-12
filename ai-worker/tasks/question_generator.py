import sys
import os
import time
import gc 
import logging
import torch
<<<<<<< HEAD
<<<<<<< HEAD
from datetime import datetime
=======
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
from datetime import datetime
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager
from langchain_core.prompts import PromptTemplate
<<<<<<< HEAD
<<<<<<< HEAD
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
=======
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea

# AI-Worker 루트 디렉토리를 찾아 sys.path에 추가
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# -----------------------------------------------------------
# [1. 모델 및 경로 설정]
# -----------------------------------------------------------
local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
if os.path.exists(local_path):
    model_path = local_path
else:
    model_path = docker_path
<<<<<<< HEAD
=======
model_path = local_path if os.path.exists(local_path) else docker_path
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea

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
<<<<<<< HEAD
<<<<<<< HEAD
# [기존 일괄 생성 태스크 삭제됨 - 실시간 생성 모드로 통합]
=======
# -----------------------------------------------------------
def generate_human_like_question(exaone, name, position, stage, guide, context_list):
    """
    ExaoneLLM 인스턴스를 사용하여 질문 생성
    """
    if not context_list:
        return f"❌ (관련 내용을 찾지 못해 질문을 생성할 수 없습니다)"

    texts = [item['text'] for item in context_list] if isinstance(context_list[0], dict) else context_list
    context_text = "\n".join([f"- {txt}" for txt in texts])
    
    try:
        # ExaoneLLM의 generate_questions 메서드 활용 (단일 질문 생성을 위해 count=1)
        # 보다 정교한 프롬프트를 위해 직접 generate 호출 가능하나, 여기서는 일관성을 위해 랩핑
        system_msg = f"당신은 15년 차 베테랑 {position} 전문 면접관이다. 지금은 면접이 한창 진행 중인 상황이다."
        user_msg = f"""지원자 {name}님에게 {stage} 단계의 면접 질문을 던지세요.

[평가 의도 - 반드시 이 관점으로 질문할 것]
{guide}

[지원자 이력서 근거]
{context_text}

[요구사항]
1. 시작은 반드시 "{name}님," 으로 부를 것.
2. **이력서에 나온 구체적인 프로젝트명/회사명/기술명을 반드시 언급**할 것.
   예: "{name}님, 이력서를 보니 오픈소스 기반 침입 탐지 프로젝트를 하셨네요~"
3. **평가 의도(guide)에 맞는 질문**을 할 것.
   - 예: guide가 "구체적인 역할과 기여도"라면 → "이 프로젝트에서 달성한 구체적인 역할과 기여도가 어떻게 되나요?"
4. 반드시 **150자 이내(두 문장 이내)**로 짧고 명확하게 물어볼 것.
5. [프로젝트], [회사명] 같은 자리표시자를 절대 사용하지 말 것.
"""

        prompt = exaone._create_prompt(system_msg, user_msg)
        output = exaone.llm(
            prompt,
            max_tokens=512,
            stop=["[|endofturn|]", "[|user|]"],
            temperature=0.4,
            echo=False
        )
        return output['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"질문 생성 실패: {e}")
        return f"면접을 이어가겠습니다. {name}님, 다음 질문입니다."

# -----------------------------------------------------------
# [4. Celery Task] - 기존 일괄 생성 태스크 (필요 시 유지)
# -----------------------------------------------------------
@shared_task(name="tasks.question_generation.generate_questions")
def generate_questions_task(interview_id, count=5, resume_id=None):
    from db import engine, Session, Resume, Interview
    from utils.exaone_llm import get_exaone_llm
    
    exaone = get_exaone_llm()
    
    with Session(engine) as session:
        # 1. 인터뷰 정보 로드 (명시적인 resume_id가 없으면 인터뷰 레코드에서 가져옴)
        if not resume_id:
            interview = session.get(Interview, interview_id)
            if interview: resume_id = interview.resume_id
            
        if not resume_id:
            logger.error(f"Resume ID not found for interview {interview_id}")
            return exaone.generate_questions("일반", count=count)

        resume = session.get(Resume, resume_id)
        if not resume:
            return exaone.generate_questions("일반", count=count)

        # 2. 이력서 파싱 데이터(header -> target_role) 추출 (데이터의 유일한 원천)
        s_data = resume.structured_data or {}
        header = s_data.get("header", {})
        target_role = header.get("target_role") or "일반"
        
        # 3. 이력서 전문(extracted_text) 가져오기
        resume_context = resume.extracted_text or ""
        
        logger.info(f"🚀 [Core Data] Name: {header.get('name')}, Target Role: {target_role}")
        
    return exaone.generate_questions(target_role, context=resume_context, count=count)
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
# [기존 일괄 생성 태스크 삭제됨 - 실시간 생성 모드로 통합]
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea

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
            
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
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


<<<<<<< HEAD
=======
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
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

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
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

            # Retriever 기반 컨텍스트 검색
            retriever = get_retriever(resume_id=interview.resume_id, top_k=2)
            retrieved_docs = retriever.invoke(query)
            rag_context = "\n".join([f"- {doc.page_content}" for doc in retrieved_docs]) if retrieved_docs else "이력서 근거 부족"

            if stage_type == "followup":
                # 꼬리질문: RAG 컨텍스트 + 이전 답변 결합
                user_stmt = select(Transcript).where(
                    Transcript.interview_id == interview_id,
                    Transcript.speaker == Speaker.USER
                ).order_by(Transcript.id.desc())
                last_user_ans = session.exec(user_stmt).first()
                user_ans_text = last_user_ans.text if last_user_ans else "이전 답변 없음"
                
                context_text = f"[지원자 이력서 관련 정보]\n{rag_context}\n\n[지원자의 이전 답변]\n{user_ans_text}"
            else:
                # 일반 AI 질문: RAG 컨텍스트 그대로 활용
                context_text = rag_context

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
            
<<<<<<< HEAD
            # AI 질문 생성 실행
            content = exaone.generate_human_like_question(
                name=candidate_name,
<<<<<<< HEAD
=======
                position=target_role,
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
                stage=stage_name,
                guide=next_stage_data.get("guide", "역량을 확인하기 위한 질문을 해주세요."),
                context_list=contexts
            )
=======
            chain = prompt | llm | output_parser
>>>>>>> 린_phase4
            
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
<<<<<<< HEAD
=======
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
            
            # AI 질문 생성 실행
            content = exaone.generate_human_like_question(
                name=candidate_name,
                position=target_role,
                stage=stage_name,
                guide=next_stage_data.get("guide", "역량을 확인하기 위한 질문을 해주세요."),
                context_list=contexts
            )
            
            # 시나리오의 카테고리를 DB Enum에 맞게 매핑
            category_raw = next_stage_data.get("category", "technical")
            category_map = {
                "certification": "technical",
                "project": "technical",
                "narrative": "behavioral",
                "problem_solving": "situational"
            }
            db_category = category_map.get(category_raw, "technical")
            
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
            save_generated_question(interview_id, content, db_category, stage_name, next_stage_data.get("guide", ""))
            return {"status": "success", "stage": stage_name, "question": content}
        except Exception as e:
            logger.error(f"실시간 질문 생성 실패: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            gc.collect()
