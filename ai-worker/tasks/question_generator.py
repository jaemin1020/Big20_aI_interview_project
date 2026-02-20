import sys
import os
import re
import gc 
import logging
import torch
from datetime import datetime
from celery import shared_task
# ... (생략: LangChain 관련 임포트)

# ==========================================
# 1. 초기 설정 및 모델 경로 최적화
# ==========================================

# [문법] sys.path.insert: 파이썬이 라이브러리를 찾을 폴더 목록 맨 앞에 "/app"을 추가합니다.
# 왜? 도커 컨테이너 내부의 소스 코드를 우선적으로 참조하기 위해서입니다.
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# [해석] 로컬 개발 환경과 도커 운영 환경의 경로가 다르기 때문에, 
# 파일이 존재하는 곳을 찾아 자동으로 model_path를 설정하는 방어적 코드입니다.
local_path = r"C:\...\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
model_path = local_path if os.path.exists(local_path) else docker_path

# ==========================================
# 2. 페르소나 설정 (Prompt Engineering)
# ==========================================

# [해석] PROMPT_TEMPLATE: LLM에게 "너는 면접관이야"라는 역할을 부여합니다.
# 특히 '특수문자 금지', '150자 이내' 같은 '절대 규칙'을 명시하여 
# 인공지능이 음성 합성(TTS)하기 좋은 깨끗한 텍스트만 뱉도록 강제합니다.
PROMPT_TEMPLATE = """... (생략) ..."""

# ==========================================
# 3. 메인 작업: 질문 생성 태스크
# ==========================================

# [문법] @shared_task: Celery 일꾼이 이 함수를 백그라운드에서 실행하도록 등록합니다.
@shared_task(name="tasks.question_generation.generate_next_question")
def generate_next_question_task(interview_id: int):
    """
    [함수의 역할] 인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    [존재 이유] 면접은 실시간 상호작용이므로, 사용자 답변이 들어오자마자 
               그에 맞는 최적의 다음 질문을 계산해야 하기 때문입니다.
    """
    from db import (engine, Session, select, ...) # [문법] 내부 임포트로 순환 참조 방지
    from utils.exaone_llm import get_exaone_llm
    
    with Session(engine) as session:
        # 1. 인터뷰 정보 로드
        interview = session.get(Interview, interview_id)
        if not interview: return {"status": "error"}

        # -------------------------------------------------------
        # [핵심 로직] 전공자 vs 비전공자(직무 전환자) 판별
        # -------------------------------------------------------
        # [해석] 지원자의 전공(Major)과 지원 직무(Target Role)를 키워드로 비교합니다.
        # 예: '국어국문학' 전공자가 '소프트웨어 개발'에 지원했다면 is_transition = True가 됩니다.
        # 이 판단에 따라 '기술 기본기'를 물을지, '직무 전환 동기'를 물을지 시나리오가 바뀝니다.
        is_transition = False
        # ... (키워드 매칭 로직) ...
        
        # -------------------------------------------------------
        # [안전장치] 중복 생성 방지 (Race Condition)
        # -------------------------------------------------------
        # [해석] AI가 질문을 던진 지 10초도 안 되었는데 또 질문 생성 요청이 오면 무시합니다.
        # 왜? 네트워크 지연 등으로 인해 동일한 요청이 두 번 들어와 AI가 혼자 북치고 장구치는 걸 막기 위함입니다.
        if last_transcript and last_transcript.speaker == Speaker.AI:
            diff = (datetime.utcnow() - last_transcript.timestamp).total_seconds()
            if diff < 10: return {"status": "skipped"}

        # -------------------------------------------------------
        # 🔍 현재 단계(Stage) 판별
        # -------------------------------------------------------
        # [해석] 대화 기록(Transcript)을 뒤져서 마지막으로 어떤 질문에 답변했는지 찾습니다.
        # '자기소개(intro)' -> '지원동기(motivation)' -> '기술면접(skill)' 순서로 
        # 면접이 물 흐르듯 진행되게 조율합니다.
        next_stage_data = get_next_stage(last_stage_name)

        # [해석] 더 이상 질문할 단계가 없으면 면접을 종료(COMPLETED) 처리하고 리포트 생성을 예약합니다.
        if not next_stage_data:
            interview.status = "COMPLETED"
            # ... 리포트 생성 트리거 ...
            return {"status": "completed"}

        # -------------------------------------------------------
        # 🚀 AI 질문 생성 (RAG + Context)
        # -------------------------------------------------------
        # [해석] 꼬리질문(followup)인 경우, 사용자가 방금 한 답변 내용을 컨텍스트에 추가합니다.
        # "방금 리액트를 써보셨다고 했는데..." 처럼 자연스러운 대화가 가능해지는 비결입니다.
        if stage_type == "followup":
            context_text = f"{profile_summary}... [최근 답변] {user_ans_text}"
        
        # [문법] LCEL(LangChain Expression Language) 체인: 
        # 프롬프트 입력 -> LLM 연산 -> 텍스트 파싱을 파이프(|) 기호로 연결한 현대적 방식입니다.
        chain = prompt | llm | output_parser
        content = chain.invoke({...})

        # -------------------------------------------------------
        # 🧹 뒷정리 (Memory Cleanup)
        # -------------------------------------------------------
        # [존재 이유] AI 모델은 메모리를 엄청나게 씁니다. 작업 하나가 끝날 때마다 
        # 쓰레기 수집(gc.collect)과 GPU 메모리 비우기를 수동으로 해줘야 서버가 안 터집니다.
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 최종 저장
        save_generated_question(interview_id, final_content, ...)