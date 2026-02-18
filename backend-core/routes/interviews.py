from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, text
from celery import Celery
from datetime import datetime
from typing import List
import logging
import os

from database import get_session
from db_models import (
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
    
    # 이력서에서 지원 직무(target_role) 가져오기
    from db_models import Resume
    resume = db.get(Resume, interview_data.resume_id)
    target_role = "일반"
    if resume and resume.structured_data:
        target_role = resume.structured_data.get("header", {}).get("target_role") or "일반"

    # 1. Interview 레코드 생성
    new_interview = Interview(
        candidate_id=current_user.id,
        position=target_role, # 추출된 직무 사용
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
    
    logger.info(f"Interview record created: ID={interview_id} (Target Role: {target_role})")
    
    # 2. 템플릿 질문 즉시 생성 (자기소개, 지원동기)
    try:
        from utils.interview_helpers import get_candidate_info, generate_template_question
        candidate_info = get_candidate_info(db, interview_data.resume_id)
        
        from config.interview_scenario import get_initial_stages
        initial_stages = get_initial_stages()
        
        for stage_config in initial_stages:
            question_text = generate_template_question(stage_config["template"], candidate_info)
            # [단계] 말머리 추가
            display_name = stage_config.get("display_name", "면접질문")
            question_text = f"[{display_name}] {question_text}"
            
            # 2-1. Question 객체 생성
            question = Question(
                content=question_text,
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.EASY,
                question_type=stage_config["stage"],
                rubric_json={"criteria": ["명확성"]},
                position=target_role
            )
            db.add(question)
            db.flush() # ID 생성을 위해 메모리 상에서만 반영
            
            # 2-2. Transcript 객체 생성
            transcript = Transcript(
                interview_id=new_interview.id,
                speaker="AI",
                text=question_text,
                question_id=question.id,
                order=stage_config.get("order", 0)
            )
            db.add(transcript)
        
        # 모든 질문/대화가 준비되었을 때 한꺼번에 커밋
        new_interview.status = InterviewStatus.LIVE
        db.add(new_interview)
        db.commit() # 여기서 실제 DB 저장 실행
        
        logger.info(f"✅ Interview setup SUCCESS for ID={interview_id}")

    except Exception as e:
        logger.error(f"❌ Interview setup CRITICAL FAILURE: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"질문 생성 중 서버 오류: {str(e)}")

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
    from db_models import Company, Resume
    for interview in interviews:
        candidate = db.get(User, interview.candidate_id)
        resume = db.get(Resume, interview.resume_id) if interview.resume_id else None
        company = db.get(Company, interview.company_id) if interview.company_id else None
        
        # 📄 이력서 추출 회사명 우선, 없으면 DB 회사명
        actual_company = "지원 기업"
        if resume and resume.structured_data:
            actual_company = resume.structured_data.get("header", {}).get("target_company") or actual_company
        
        if (not actual_company or actual_company == "지원 기업") and company:
            actual_company = company.company_name
            
        result.append({
            "id": interview.id,
            "candidate_id": interview.candidate_id,
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "position": interview.position,
            "company_name": actual_company, # 회사명 추가
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
    # Transcript 테이블에서 AI 발화(질문) 목록 조회
    # Speaker.AI(Enum) 대신 문자열 'AI'로 직접 비교하여 쿼리 안전성 확보
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id,
        Transcript.speaker == "AI"
    ).order_by(Transcript.id)

    results = db.exec(stmt).all()
    
    # 인터뷰 상태 정보 가져오기
    interview = db.get(Interview, interview_id)
    
    return {
        "status": interview.status if interview else "UNKNOWN",
        "questions": [
            {
                "id": t.question_id,
                "content": t.text,
                "order": t.order,
                "timestamp": t.timestamp,
                "audio_url": None # 오디오 URL은 필요 시 Question 테이블에서 따로 가져올 수 있음
            }
            for t in results
        ]
    }


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
    
    # 🔗 데이터 원본(DB) 조회
    from db_models import Company, Resume
    interview = db.get(Interview, interview_id)
    resume = db.get(Resume, interview.resume_id) if interview and interview.resume_id else None
    company = db.get(Company, interview.company_id) if interview and interview.company_id else None
    candidate = db.get(User, interview.candidate_id) if interview else None

    # 📄 이력서 및 프로필에서 실제 데이터 추출
    res_data = resume.structured_data if resume and resume.structured_data else {}
    res_header = res_data.get("header", {})
    
    cand_name = res_header.get("name") or (candidate.full_name if candidate else "지원자")
    actual_position = res_header.get("target_role") or (interview.position if interview else "직무 미상")
    
    # 회사명: 이력서 추출값 -> DB 저장값 -> '지원 기업' (폴백)
    actual_company = res_header.get("target_company")
    if not actual_company or str(actual_company).strip() == "":
        actual_company = company.company_name if (company and company.company_name) else "지원 기업"
    
    # 🔄 데이터 매핑 (EvaluationReportResponse 형식에 맞춤)
    report_dict = report.dict()
    report_dict["position"] = actual_position
    report_dict["company_name"] = actual_company
    report_dict["candidate_name"] = cand_name
    report_dict["interview_date"] = interview.start_time if interview else report.created_at
    
    # [핵심] AI가 분석한 상세 피드백 및 강점/보완점 필드 최상위 노출
    details = report.details_json or {}
    report_dict["technical_feedback"] = details.get("technical_feedback") or report.summary_text # 폴백
    report_dict["experience_feedback"] = details.get("experience_feedback")
    report_dict["problem_solving_feedback"] = details.get("problem_solving_feedback")
    report_dict["communication_feedback"] = details.get("communication_feedback")
    report_dict["responsibility_feedback"] = details.get("responsibility_feedback")
    report_dict["growth_feedback"] = details.get("growth_feedback")
    
    report_dict["strengths"] = details.get("strengths", [])
    report_dict["improvements"] = details.get("improvements", [])

    return report_dict

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
    
    logger.info(f"🆕 Creating REALTIME interview session for user {current_user.id} using Resume ID: {interview_data.resume_id}")
    
    # 0. 지원자 정보 조회 (이력서 기반으로 직무/이름 가져오기)
    from utils.interview_helpers import get_candidate_info
    candidate_info = get_candidate_info(db, interview_data.resume_id)
    target_role = candidate_info.get("target_role", "일반")
    candidate_name = candidate_info.get("candidate_name", "지원자")

    # 1. Interview 레코드 생성
    new_interview = Interview(
        candidate_id=current_user.id,
        position=target_role, # 이력서 추출 값으로 고정
        company_id=interview_data.company_id,
        resume_id=interview_data.resume_id,
        status=InterviewStatus.IN_PROGRESS,
        scheduled_time=interview_data.scheduled_time,
        start_time=datetime.utcnow()
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    db.flush() # ID를 얻기 위해 flush
    
    logger.info(f"Realtime Interview created: ID={new_interview.id}, Candidate={candidate_name}, Target Role={target_role}")
    
    # 2. 템플릿 질문 즉시 생성
    try:
        from utils.interview_helpers import generate_template_question
        
        # 시나리오에서 초기 템플릿 가져오기
        try:
            from config.interview_scenario import get_initial_stages
            initial_stages = get_initial_stages()
        except ImportError:
            # 폴백: 시나리오 로드 실패 시 강제 생성
            logger.warning("⚠️ Could not import interview_scenario, using hardcoded fallback questions.")
            initial_stages = [
                {"stage": "intro", "template": "{candidate_name} 지원자님, 간단히 자기소개 부탁드립니다.", "order": 1},
                {"stage": "motivation", "template": "{candidate_name} 지원자님, 지원동기 말씀해주세요.", "order": 2}
            ]
        
        for stage_config in initial_stages:
            question_text = generate_template_question(
                stage_config.get("template", "{candidate_name}님 시작해주세요."),
                candidate_info
            )
            # [단계] 말머리 추가
            display_name = stage_config.get("display_name", "면접질문")
            question_text = f"[{display_name}] {question_text}"
            
            # Question 저장
            question = Question(
                content=question_text,
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.EASY,
                question_type=stage_config.get("stage", "general"),
                rubric_json={"criteria": ["명확성"]},
                position=target_role
            )
            db.add(question)
            db.flush() # question.id를 얻기 위해 flush
            
            # Transcript 에 AI 발화 기록
            transcript = Transcript(
                interview_id=new_interview.id,
                speaker="AI",
                text=question_text,
                question_id=question.id,
                order=stage_config.get("order", 0)
            )
            db.add(transcript)
        
        # 일괄 커밋
        db.commit()
        logger.info(f"✅ Realtime interview setup SUCCESS for ID={new_interview.id}")
        
    except Exception as e:
        logger.error(f"❌ Realtime interview setup FAILED: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 생성 실패: {str(e)}"
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