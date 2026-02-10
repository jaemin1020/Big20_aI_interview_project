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
평가 의도: {guide}
지원자 이력서 근거 (RAG):
{context_text}

[요구사항]
1. 시작은 반드시 "{name}님," 으로 부를 것.
2. 이력서 내용을 바탕으로 이해하기 쉬운 **간결한 질문 1개**만 던질 것.
3. 반드시 **150자 이내(두 문장 이내)**로 짧고 명확하게 물어볼 것. 사족 금지.
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
def generate_questions_task(position, interview_id, count=5, resume_id=1):
    from utils.exaone_llm import get_exaone_llm
    exaone = get_exaone_llm()
    
    # ... (생략 가능하나 호환성을 위해 유지 시에는 exaone.generate_questions 사용 권장)
    return exaone.generate_questions(position, count=count)

# -----------------------------------------------------------
# [5. Celery Task] - 실시간 1개씩 생성하는 태스크 (수정 완료)
# -----------------------------------------------------------
@shared_task(name="tasks.question_generation.generate_next_question")
def generate_next_question_task(interview_id: int):
    logger.info(f"🔥 [START] generate_next_question_task for Interview {interview_id}")
    from db import engine, Session, select, save_generated_question
    from models import Interview, Transcript, Speaker, Question
    from config.interview_scenario import get_stage_by_name, get_next_stage
    from utils.exaone_llm import get_exaone_llm
    
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if not interview: return
            
        # 🔍 마지막 단계 탐지 최적화 (순서 기반이 아닌 ID 기반 최신 데이터 조회)
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker == Speaker.AI
        ).order_by(Transcript.id.desc()) # ID가 가장 큰 것이 절대적으로 최신
        last_ai_transcript = session.exec(stmt).first()
        
        last_stage_name = None
        if last_ai_transcript and last_ai_transcript.question_id:
            last_q = session.get(Question, last_ai_transcript.question_id)
            if last_q:
                # 1순위: DB에 저장된 타입 정보 사용
                last_stage_name = last_q.question_type
                
                # 2순위 (Fallback): 저장된 타입이 없으면 텍스트 내용으로 유추 (더 많은 키워드 추가)
                if not last_stage_name:
                    content = last_q.content
                    if "자기소개" in content: last_stage_name = "intro"
                    elif "지원 동기" in content or "지원하게 된" in content: last_stage_name = "motivation"
                    elif "기술" in content or "스킬" in content or "도구" in content: last_stage_name = "skill"
                    elif "프로젝트" in content or "경험" in content: last_stage_name = "experience"
                    elif "어려움" in content or "해결" in content: last_stage_name = "problem_solving"
        
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
            
            # 컨텍스트 준비 (일반 AI 질문 vs 꼬리질문)
            contexts = []
            if stage_type == "followup":
                # 꼬리질문의 경우 RAG 대신 '직전 답변'을 컨텍스트로 사용
                user_stmt = select(Transcript).where(
                    Transcript.interview_id == interview_id,
                    Transcript.speaker == Speaker.USER
                ).order_by(Transcript.id.desc())
                last_user_ans = session.exec(user_stmt).first()
                if last_user_ans:
                    contexts = [{"text": f"이전 답변: {last_user_ans.text}", "meta": {"category": "followup"}}]
                    logger.info(f"📌 Follow-up context prepared from last answer.")
            
            # RAG 검색 (꼬리질문이 아니거나, 꼬리질문인데 컨텍스트를 못 찾은 경우)
            if not contexts:
                from .rag_retrieval import retrieve_context
                query_tmpl = next_stage_data.get("query_template", "{target_role}")
                query = query_tmpl.format(target_role=interview.position)
                contexts = retrieve_context(query, resume_id=interview.resume_id, top_k=3)
            
            from utils.interview_helpers import get_candidate_info
            from db import Resume
            resume = session.get(Resume, interview.resume_id)
            c_info = get_candidate_info(resume.structured_data if resume else {})
            
            content = generate_human_like_question(
                exaone, c_info.get("candidate_name", "지원자"), interview.position, 
                stage_name, next_stage_data.get("guide", ""), contexts
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
            
            save_generated_question(interview_id, content, db_category, stage_name, next_stage_data.get("guide", ""))
            return {"status": "success", "stage": stage_name, "question": content}
        except Exception as e:
            logger.error(f"실시간 질문 생성 실패: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            gc.collect()
