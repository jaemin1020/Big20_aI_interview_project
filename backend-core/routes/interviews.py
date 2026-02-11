from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, text
from celery import Celery
from datetime import datetime
from typing import List
import logging
import os

from database import get_session
from models import (
    User, Interview, InterviewCreate, InterviewResponse, InterviewStatus,
    Question, QuestionCategory, QuestionDifficulty,
    Transcript, TranscriptCreate, Speaker,
    EvaluationReport, EvaluationReportResponse
)
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/interviews", tags=["interviews"])
logger = logging.getLogger("Interview-Router")

# Celery 설정 (main.py와 공유 필요, 또는 별도 설정 파일로 분리 추천)
# 여기서는 동일하게 설정
celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# 면접 생성
@router.post("", response_model=InterviewResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접 세션 생성 및 질문 생성
    
    Args:
        interview_data (InterviewCreate): 면접 생성 정보
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        current_user (User, optional): 현재 사용자. Defaults to Depends(get_current_user).
        
    Returns:
        InterviewResponse: 면접 생성 정보
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    
    logger.info(f"🆕 Creating interview session for user {current_user.id} using Resume ID: {interview_data.resume_id}")
    
    # 0. 이력서에서 직무 정보 가져오기 (프론트엔드 입력 대신 이력서 기반)
    from models import Resume
    resume = db.get(Resume, interview_data.resume_id)
    auto_position = "일반"
    if resume and resume.structured_data:
        auto_position = resume.structured_data.get("header", {}).get("target_role") or "일반"

    # 1. Interview 레코드 생성
    new_interview = Interview(
        candidate_id=current_user.id,
        position=auto_position, # 자동으로 찾아낸 직무 저장
        company_id=interview_data.company_id,
        resume_id=interview_data.resume_id,
        status=InterviewStatus.SCHEDULED,
        scheduled_time=interview_data.scheduled_time,
        start_time=datetime.utcnow()
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    
    interview_id = new_interview.id
    
    logger.info(f"Interview record created: ID={interview_id} (Detected Position: {auto_position})")
    
    try:
        logger.info("Requesting question generation from AI-Worker...")
        task = celery_app.send_task(
            "tasks.question_generation.generate_questions",
            args=[new_interview.id, 5], # position 인자 제거
            queue="gpu_queue"
        )
        generated_data = task.get(timeout=180)
        logger.info(f"Received {len(generated_data)} questions from AI-Worker")
        
        # Format check
        if generated_data and isinstance(generated_data[0], dict):
            generated_questions = generated_data
        else:
            generated_questions = [{"text": q, "audio_url": None} for q in generated_data]
        
    except Exception as e:
        logger.warning(f"AI-Worker question generation failed ({e}). Using fallback questions.")
        fallback_texts = [
            f"{interview_data.position} 직무에 지원하게 된 동기를 구체적으로 말씀해주세요.",
            "가장 도전적이었던 프로젝트 경험과 그 과정에서 얻은 교훈은 무엇인가요?",
            f"{interview_data.position}로서 본인의 가장 큰 강점과 보완하고 싶은 점은 무엇인가요?",
            "갈등 상황을 해결했던 구체적인 사례가 있다면 설명해주세요.",
            "향후 5년 뒤의 커리어 목표는 무엇인가요?"
        ]
        generated_questions = [{"text": q, "audio_url": None} for q in fallback_texts]


    # 3. Questions 및 Transcript 테이블에 저장
    try:
        for i, item in enumerate(generated_questions):
            q_text = item["text"]
            q_audio = item.get("audio_url")

            # 3-1. 질문 은행에 저장
            question = Question(
                content=q_text,
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.EASY,
                question_type="intro" if i == 0 else "skill", # 'technical' 대신 시나리오 표준인 'skill' 사용
                rubric_json={
                    "criteria": ["구체성", "직무 적합성", "논리력"], 
                    "weight": {"content": 0.5, "communication": 0.5},
                    "audio_url": q_audio 
                },
                position=interview_data.position
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            
            # Transcript 저장 (Raw SQL로 관계 꼬입 원칙적 차단)
            db.execute(
                text("""
                    INSERT INTO transcripts (interview_id, speaker, text, timestamp, question_id, "order")
                    VALUES (:i_id, :spk, :txt, :ts, :q_id, :ord)
                """),
                {
                    "i_id": interview_id,
                    "spk": Speaker.AI,
                    "txt": q_text,
                    "ts": datetime.utcnow(),
                    "q_id": question.id,
                    "ord": i
                }
            )
            db.commit()
        
        # 면접 상태 업데이트: LIVE
        new_interview.status = InterviewStatus.LIVE
        db.add(new_interview)
        db.commit()
        db.refresh(new_interview)
        
        logger.info(f"✅ Realtime interview setup completed for ID={interview_id}")
        
    except Exception as e:
        logger.error(f"❌ Critical Error in interview creation: {e}")
        db.rollback()
        # 실패한 면접은 삭제 시도 (에러 무시)
        try:
            db.execute(text("DELETE FROM interviews WHERE id = :i_id"), {"i_id": interview_id})
            db.commit()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"면접 생성 실패: {str(e)}")

    # 응답 보내기 전 마지막 상태 확인
    return InterviewResponse(
        id=new_interview.id,
        candidate_id=new_interview.candidate_id,
        position=new_interview.position,
        status=new_interview.status,
        start_time=new_interview.start_time,
        end_time=new_interview.end_time,
        overall_score=new_interview.overall_score
    )

# 전체 인터뷰 목록 조회 (리크루터용 + 본인 조회)
@router.get("")
async def get_all_interviews(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    전체 인터뷰 목록 조회
    
    Args:
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        current_user (User, optional): 현재 사용자. Defaults to Depends(get_current_user).
        
    Returns:
        List[InterviewResponse]: 인터뷰 목록
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    if current_user.role not in ["recruiter", "admin"]:
        stmt = select(Interview).where(
            Interview.candidate_id == current_user.id
        ).order_by(Interview.created_at.desc())
    else:
        stmt = select(Interview).order_by(Interview.created_at.desc())
    
    interviews = db.exec(stmt).all()
    
    result = []
    for interview in interviews:
        candidate = db.get(User, interview.candidate_id)
        result.append({
            "id": interview.id,
            "candidate_id": interview.candidate_id,
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "position": interview.position,
            "status": interview.status,
            "created_at": interview.created_at,
            "start_time": interview.start_time,
            "end_time": interview.end_time,
            "overall_score": interview.overall_score
        })
    return result

# 면접 질문 조회
@router.get("/{interview_id}/questions")
async def get_interview_questions(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접의 질문 목록 조회
    
    Args:
        interview_id (int): 면접 ID
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        current_user (User, optional): 현재 사용자. Defaults to Depends(get_current_user).
        
    Returns:
        List[InterviewResponse]: 면접 질문 목록
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    # Question 테이블과 조인하여 audio_url 가져오기
    stmt = select(Transcript, Question).join(Question, Transcript.question_id == Question.id).where(
        Transcript.interview_id == interview_id,
        Transcript.speaker == Speaker.AI
    ).order_by(Transcript.timestamp)
    
    results = db.exec(stmt).all()
    
    return [
        {
            "id": t.question_id,
            "content": t.text,
            "order": t.order,
            "timestamp": t.timestamp,
            "audio_url": q.rubric_json.get("audio_url") if q.rubric_json else None
        }
        for t, q in results
    ]


# 면접의 전체 대화 기록 조회
@router.get("/{interview_id}/transcripts")
async def get_interview_transcripts(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접의 전체 대화 기록 조회
    
    Args:
        interview_id (int): 면접 ID
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        current_user (User, optional): 현재 사용자. Defaults to Depends(get_current_user).
        
    Returns:
        List[InterviewResponse]: 면접 대화 기록 목록
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id
    ).order_by(Transcript.timestamp)
    
    transcripts = db.exec(stmt).all()
    
    return [
        {
            "id": t.id,
            "speaker": t.speaker,
            "text": t.text,
            "timestamp": t.timestamp,
            "sentiment_score": t.sentiment_score,
            "emotion": t.emotion
        }
        for t in transcripts
    ]

# 면접 완료 처리
@router.post("/{interview_id}/complete")
async def complete_interview(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접 완료 처리
    
    Args:
        interview_id (int): 면접 ID
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        current_user (User, optional): 현재 사용자. Defaults to Depends(get_current_user).
        
    Returns:
        dict: 면접 완료 정보
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview.status = InterviewStatus.COMPLETED
    interview.end_time = datetime.utcnow()
    db.add(interview)
    db.commit()
    
    celery_app.send_task(
        "tasks.evaluator.generate_final_report",
        args=[interview_id]
    )
    return {"status": "completed", "interview_id": interview_id}

# 평가 리포트 조회
@router.get("/{interview_id}/report", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    평가 리포트 조회
    
    Args:
        interview_id (int): 면접 ID
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        current_user (User, optional): 현재 사용자. Defaults to Depends(get_current_user).
        
    Returns:
        EvaluationReportResponse: 평가 리포트
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    stmt = select(EvaluationReport).where(
        EvaluationReport.interview_id == interview_id
    )
    report = db.exec(stmt).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet available")
    
    return report

# --- Transcript Route (별도 파일로 할 수도 있지만 interview와 밀접하므로 여기에 포함) ---
# 기존 main.py에서는 /transcripts 였지만 여기서는 /interviews 하위가 아님.
# 따라서 별도 라우터(`transcripts_router`)로 분리하거나, prefix 없는 별도 라우터를 정의해야 함.
# 편의상 여기서는 router 외에 별도 router를 정의하지 않고,
# /transcripts 엔드포인트를 위해 APIRouter를 하나 더 만들지 않고, 
# main.py에서 transcript 관련은 별도 라우터 파일(`routes/transcripts.py`)로 빼는 게 깔끔함.
# 일단 여기서는 Interview 관련만 처리.


# ============================================================================
# 실시간 대화형 면접 API (신규)
# ============================================================================

@router.post("/realtime", response_model=InterviewResponse)
async def create_realtime_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    실시간 대화형 면접 생성
    - 템플릿 질문 2개(자기소개, 지원동기)만 즉시 생성하여 반환
    - 대기 시간: 0초
    """
    
    logger.info(f"🆕 Creating REALTIME interview session for user {current_user.id}. Requested Position: {interview_data.position}")
    
    # 1. Interview 레코드 생성
    new_interview = Interview(
        candidate_id=current_user.id,
        position=interview_data.position,
        company_id=interview_data.company_id,
        resume_id=interview_data.resume_id,
        status=InterviewStatus.IN_PROGRESS,
        scheduled_time=interview_data.scheduled_time,
        start_time=datetime.utcnow()
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    
    logger.info(f"Realtime Interview created: ID={new_interview.id}, Position={new_interview.position}")
    
    # 2. 템플릿 질문 즉시 생성
    try:
        from utils.interview_helpers import get_candidate_info, generate_template_question
        
        # 지원자 정보 조회
        candidate_info = get_candidate_info(db, interview_data.resume_id)
        logger.info(f"Candidate: {candidate_info['candidate_name']}, Role: {candidate_info['target_role']}")
        
        # 시나리오에서 초기 템플릿 가져오기
        import sys
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "ai-worker", "config")
        if config_path not in sys.path:
            sys.path.append(config_path)
        
        from interview_scenario import get_initial_stages
        
        initial_stages = get_initial_stages()
        
        for stage_config in initial_stages:
            # 템플릿에 변수 삽입
            question_text = generate_template_question(
                stage_config["template"],
                candidate_info
            )
            
            # Question 저장
            question = Question(
                content=question_text,
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.EASY,
                question_type=stage_config["stage"], # 단계 매칭을 위해 추가
                rubric_json={
                    "criteria": ["명확성", "진정성", "직무 이해도"],
                    "weight": {"content": 0.6, "communication": 0.4}
                },
                position=interview_data.position
            )
            db.add(question)
            db.commit()  # 즉시 커밋
            db.refresh(question)
            
            # Transcript에 AI 발화 기록 (별도 세션 사용)
            from database import engine
            from sqlmodel import Session as NewSession
            with NewSession(engine) as transcript_session:
                transcript = Transcript(
                    interview_id=new_interview.id,
                    speaker=Speaker.AI,
                    text=question_text,
                    question_id=question.id,
                    order=stage_config["order"] - 1
                )
                transcript_session.add(transcript)
                transcript_session.commit()
        
        logger.info(f"✅ Generated {len(initial_stages)} template questions immediately")
        
    except Exception as e:
        logger.error(f"❌ Template question generation failed: {e}")
        db.delete(new_interview)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"면접 질문 생성에 실패했습니다: {str(e)}"
        )
    
    return InterviewResponse(
        id=new_interview.id,
        candidate_id=new_interview.candidate_id,
        position=new_interview.position,
        status=new_interview.status,
        start_time=new_interview.start_time,
        end_time=new_interview.end_time,
        overall_score=new_interview.overall_score
    )
