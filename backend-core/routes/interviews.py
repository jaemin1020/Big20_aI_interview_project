from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, text
from datetime import datetime, timezone, timedelta

# KST (Korea Standard Time) 설정
KST = timezone(timedelta(hours=9))

def get_kst_now():
    return datetime.now(KST).replace(tzinfo=None)

from typing import List
import logging
import os
import base64
import json
from pathlib import Path

from database import get_session
from db_models import (
    User, Interview, InterviewCreate, InterviewResponse, InterviewStatus,
    Question, QuestionCategory, QuestionDifficulty,
    Transcript, TranscriptCreate, Speaker,
    EvaluationReport, EvaluationReportResponse
)
from utils.auth_utils import get_current_user
from utils.redis_cache import redis_client

router = APIRouter(prefix="/interviews", tags=["interviews"])
logger = logging.getLogger("Interview-Router")
logger.setLevel(logging.INFO)

# Celery
from celery_app import celery_app

# TTS 오디오 저장 디렉토리 (백엔드와 ai-worker 공유 볼륨)
TTS_UPLOAD_DIR = Path("/app/uploads/tts")
TTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 백엔드 외부 URL (VITE_API_URL 환경변수 사용 불가 시 기본값)
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

def _fire_tts_for_question(question_id: int, question_text: str) -> None:
    """설명:
        질문에 대한 TTS 태스크를 실행하고 생성된 WAV 파일을 공유 볼륨(uploads/tts/)에 저장합니다.
        문장 내의 [단계] 태그를 자동으로 제거하여 합성하며, 이미 파일이 존재하는 경우 중복 생성을 방지합니다.
    """
    filename = f"q_{question_id}.wav"
    filepath = TTS_UPLOAD_DIR / filename

    # 이미 생성된 파일이면 스킵
    if filepath.exists():
        return

    # [Idempotency] Redis 분산 락 체크 (중복 요청 방지)
    if redis_client:
        lock_key = f"lock:tts:{question_id}"
        if redis_client.get(lock_key):
            logger.debug(f"🛑 [TTS] 요청 스킵 (이미 처리 중): {filename}")
            return
        # 60초 동안 락 설정 (태스크가 큐에 머무는 시간 고려)
        redis_client.setex(lock_key, 60, "in_progress")

    # [...] 미리보기 태그 제거 (TTS가 읽는 클린 텍스트)
    clean_text = question_text
    if question_text.startswith('[') and ']' in question_text:
        parts = question_text.split(']', 1)
        if len(parts) > 1:
            clean_text = parts[1].strip()

    try:
        # [fire-and-forget] TTS 태스크는 파일을 직접 저장하므로 결과를 기다릴 필요 없음
        celery_app.send_task(
            "tasks.tts.synthesize",
            args=[clean_text],
            kwargs={"language": "ko", "question_id": question_id},
            queue="cpu_queue"
        )
        logger.info(f"🔊 [TTS] 비동기 음성 생성 요청 완료: {filename} (백그라운드 처리 중)")
    except Exception as e:
        logger.warning(f"[TTS] question_id={question_id} 생성 요청 실패: {e}")

# 면접 생성
@router.post("", response_model=InterviewResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접 세션 생성 및 질문 생성
    """
    logger.info(f"🆕 Creating interview session for user {current_user.id} using Resume ID: {interview_data.resume_id}")

    # 이력서에서 지원 직무(target_role) 및 회사명 가져오기
    from db_models import Resume, Company
    import json
    resume = db.get(Resume, interview_data.resume_id)
    target_role = "일반"
    extracted_company_id = interview_data.company_id

    if resume and resume.structured_data:
        s_data = resume.structured_data
        if isinstance(s_data, str):
            try:
                s_data = json.loads(s_data)
                if isinstance(s_data, str): 
                    s_data = json.loads(s_data)
            except Exception as e:
                logger.error(f"Failed to parse structured_data for auto-match: {e}")
                s_data = {}

        header = s_data.get("header", {}) if isinstance(s_data, dict) else {}
        target_role = header.get("target_role") or "일반"

        if not extracted_company_id:
            target_company_name = header.get("target_company")
            logger.info(f"🔍 Extracted company name from resume: '{target_company_name}'")

            if target_company_name:
                stripped_name = str(target_company_name).strip()
                from sqlalchemy import func
                stmt = select(Company).where(func.lower(Company.company_name) == func.lower(stripped_name))
                found_company = db.exec(stmt).first()
                if found_company:
                    extracted_company_id = found_company.id
                    logger.info(f"🏢 Company auto-matched: '{stripped_name}' -> ID: {extracted_company_id}")
                else:
                    logger.warning(f"⚠️ No company found matching name: '{stripped_name}'")

    logger.info(f"💾 Final company_id to be saved: '{extracted_company_id}'")

    # 1. Interview 레코드 생성
    new_interview = Interview(
        candidate_id=current_user.id,
        position=target_role, 
        company_id=extracted_company_id, 
        resume_id=interview_data.resume_id,
        status=InterviewStatus.SCHEDULED,
        scheduled_time=interview_data.scheduled_time,
        start_time=get_kst_now(),
        created_at=get_kst_now()
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    interview_id = new_interview.id
    logger.info(f"Interview record created: ID={interview_id} (Target Role: {target_role})")

    # 2. 템플릿 질문 즉시 생성
    try:
        from utils.interview_helpers import get_candidate_info, generate_template_question, check_if_transition
        candidate_info = get_candidate_info(db, interview_data.resume_id)
        is_transition = check_if_transition(candidate_info.get("major", ""), target_role)

        if is_transition:
            from config.interview_scenario_transition import get_initial_stages
            logger.info(f"✨ [TRANSITION] Career change detected ({candidate_info.get('major')} -> {target_role}). Using transition scenario.")
        else:
            from config.interview_scenario import get_initial_stages
            logger.info("✅ [STANDARD] Regular career path detected. Using standard scenario.")

        initial_stages = get_initial_stages()

        for stage_config in initial_stages:
            question_text = generate_template_question(stage_config["template"], candidate_info)
            display_name = stage_config.get("display_name", "면접질문")
            intro_msg = stage_config.get("intro_sentence", "")
            question_text = f"{intro_msg} {question_text}" if intro_msg else question_text

            # 2-1. Question 객체 생성
            question = Question(
                content=question_text,
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.EASY,
                question_type=stage_config["stage"],
                rubric_json={"criteria": ["명확성"]},
                position=target_role,
                created_at=get_kst_now()
            )
            db.add(question)
            db.flush() 

            # 2-1. Question 객체 생성 (TTS 비동기 요청 포함)
            _fire_tts_for_question(question.id, question_text)

            # 2-2. Transcript 객체 생성
            transcript = Transcript(
                interview_id=new_interview.id,
                speaker="AI",
                text=question_text,
                question_id=question.id,
                order=stage_config.get("order", 0),
                timestamp=get_kst_now()
            )
            db.add(transcript)
            logger.info(f"✨ [PRE-GENERATE] Stage '{stage_config['stage']}' (Order {stage_config['order']}) created at backend.")

        new_interview.status = InterviewStatus.LIVE
        db.add(new_interview)
        db.commit() 

        logger.info(f"✅ Interview setup SUCCESS for ID={interview_id}")

        try:
            celery_app.send_task(
                "tasks.question_generation.preload_model",
                queue="gpu_queue"
            )
            logger.info("🔥 [Preload] EXAONE 모델 사전 로딩 태스크 발사 완료 (비동기)")
        except Exception as e:
            logger.warning(f"[Preload] 모델 사전 로딩 태스크 전송 실패 (무시): {e}")

    except Exception as e:
        logger.error(f"❌ Interview setup CRITICAL FAILURE: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"질문 생성 중 서버 오류: {str(e)}")

    return InterviewResponse(
        id=new_interview.id,
        candidate_id=new_interview.candidate_id,
        position=new_interview.position,
        status=new_interview.status,
        start_time=new_interview.start_time,
        end_time=new_interview.end_time,
        overall_score=new_interview.overall_score
    )

# 전체 인터뷰 목록 조회 
@router.get("")
async def get_all_interviews(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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
            "company_name": actual_company, 
            "status": interview.status,
            "created_at": interview.created_at,
            "start_time": interview.start_time,
            "end_time": interview.end_time,
            "overall_score": interview.overall_score,
            "resume_id": interview.resume_id
        })
    return result

# 면접 질문 조회 (★ 프론트엔드가 폴링할 핵심 API)
@router.get("/{interview_id}/questions")
async def get_interview_questions(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접의 질문 목록 조회
    프론트엔드에서 주기적으로 호출(Polling)하여 새 질문과 TTS 음성 파일 상태를 확인합니다.
    """
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id,
        Transcript.speaker == "AI"
    ).order_by(Transcript.id)

    results = db.exec(stmt).all()
    interview = db.get(Interview, interview_id)

    def get_audio_url(question_id: int, question_text: str) -> str | None:
        """TTS 파일 존재 시 URL 반환, 없으면 TTS 트리거 후 None 반환"""
        if question_id is None:
            return None
        filepath = TTS_UPLOAD_DIR / f"q_{question_id}.wav"
        if filepath.exists():
            timestamp = int(get_kst_now().timestamp())
            url = f"{BACKEND_PUBLIC_URL}/uploads/tts/q_{question_id}.wav?t={timestamp}"
            return url
        
        logger.warning(f"⏳ [TTS Missing] ID: {question_id}, Path: {filepath}")
        import threading
        threading.Thread(
            target=_fire_tts_for_question,
            args=(question_id, question_text),
            daemon=True
        ).start()
        return None

    return {
        "status": interview.status if interview else "UNKNOWN",
        "questions": [
            {
                "id": t.question_id,
                "content": t.text,
                "order": t.order,
                "timestamp": t.timestamp,
                "audio_url": get_audio_url(t.question_id, t.text)
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
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    interview.status = InterviewStatus.COMPLETED
    interview.end_time = get_kst_now()
    db.add(interview)
    db.commit()

    celery_app.send_task(
        "tasks.evaluator.generate_final_report",
        args=[interview_id],
        queue='gpu_queue'
    )
    return {"status": "completed", "interview_id": interview_id}

# 행동 분석 점수 저장
@router.patch("/{interview_id}/behavior-scores")
async def save_behavior_scores(
    interview_id: int,
    request: dict,
    db: Session = Depends(get_session),
):
    import json as json_lib

    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    averages = request.get("averages", {})
    interview.emotion_summary = {
        "averages": averages,
        "interview_duration_sec": request.get("interview_duration_sec"),
        "total_questions": request.get("total_questions")
    }
    interview.overall_score = averages.get("total")
    db.add(interview)

    per_question = request.get("per_question", [])
    if per_question:
        user_transcripts = db.exec(
            select(Transcript).where(
                Transcript.interview_id == interview_id,
                Transcript.speaker == SpeakerEnum.USER
            ).order_by(Transcript.id)
        ).all()

        for i, q_score in enumerate(per_question):
            if i < len(user_transcripts):
                user_transcripts[i].emotion = json_lib.dumps(q_score, ensure_ascii=False)
                user_transcripts[i].sentiment_score = q_score.get("total")
                db.add(user_transcripts[i])
                logger.info(f"  📝 Q{q_score['q_idx']} → transcript[{user_transcripts[i].id}].emotion 저장")

    db.commit()
    logger.info(f"✅ [behavior-scores] Interview {interview_id} 행동 분석 점수 저장 완료")
    return {"status": "saved", "interview_id": interview_id}

# 평가 리포트 조회
@router.get("/{interview_id}/report", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EvaluationReport).where(
        EvaluationReport.interview_id == interview_id
    )
    report = db.exec(stmt).first()

    from db_models import Company, Resume
    interview = db.get(Interview, interview_id)

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    resume = db.get(Resume, interview.resume_id) if interview.resume_id else None
    company = db.get(Company, interview.company_id) if interview.company_id else None
    candidate = db.get(User, interview.candidate_id) if interview.candidate_id else None

    res_data = {}
    if resume and resume.structured_data:
        if isinstance(resume.structured_data, str):
            import json
            try: res_data = json.loads(resume.structured_data)
            except: res_data = {}
        else:
            res_data = resume.structured_data

    res_header = res_data.get("header", {})

    cand_name = res_header.get("name") or (candidate.full_name if candidate else "지원자")
    actual_position = res_header.get("target_role") or (interview.position if interview.position != "일반" else None) or "전문 직무"

    actual_company = res_header.get("target_company")
    if not actual_company or str(actual_company).strip() == "":
        actual_company = company.company_name if (company and company.company_name) else "지원 기업"

    if not report:
        now = get_kst_now()
        return {
            "id": 0,
            "interview_id": interview_id,
            "technical_score": 0, "communication_score": 0, "cultural_fit_score": 0,
            "summary_text": "AI가 현재 면접 내용을 상세 분석하고 있습니다. 잠시만 기다려 주세요.",
            "details_json": {},          
            "created_at": now,           
            "position": actual_position,
            "company_name": actual_company,
            "candidate_name": cand_name,
            "interview_date": interview.start_time or now,
            "technical_feedback": "분석이 완료되면 여기에 표시됩니다.",
            "experience_feedback": "데이터 분석 중...",
            "problem_solving_feedback": "데이터 분석 중...",
            "communication_feedback": "의사소통 역량을 분석 중입니다.",
            "responsibility_feedback": "책임감 및 조직 적합성을 분석 중입니다.",
            "growth_feedback": "성장 가능성을 분석 중입니다.",
            "strengths": ["분석 진행 중"],
            "improvements": ["분석 진행 중"]
        }

    try:
        report_dict = report.model_dump()
    except AttributeError:
        report_dict = report.dict()
        
    report_dict["position"] = actual_position
    report_dict["company_name"] = actual_company
    report_dict["candidate_name"] = cand_name
    report_dict["interview_date"] = interview.start_time if interview else report.created_at

    details = report.details_json or {}

    report_dict["responsibility_score"] = details.get("responsibility_score", 0)
    report_dict["growth_score"] = details.get("growth_score", 0)
    report_dict["experience_score"] = details.get("experience_score", 0)
    report_dict["problem_solving_score"] = details.get("problem_solving_score", 0)

    report_dict["technical_feedback"] = details.get("technical_feedback") or report.summary_text or "기술 역량 분석 결과가 생성 중입니다."
    report_dict["experience_feedback"] = details.get("experience_feedback") or "프로젝트 경험에 대한 AI 분석 결과입니다."
    report_dict["problem_solving_feedback"] = details.get("problem_solving_feedback") or "문제 해결 능력에 대한 AI 분석 결과입니다."
    report_dict["communication_feedback"] = details.get("communication_feedback") or "의사소통 스타일에 대한 AI 분석 결과입니다."
    report_dict["responsibility_feedback"] = details.get("responsibility_feedback") or "지원자의 직업 윤리 및 책임감에 대한 상세 분석 내용입니다."
    report_dict["growth_feedback"] = details.get("growth_feedback") or "향후 발전 가능성 및 인재상 부합도에 대한 분석 내용입니다."

    report_dict["strengths"] = details.get("strengths") or ["성실한 답변 태도", "직무 기초 역량 보유"]
    report_dict["improvements"] = details.get("improvements") or ["구체적인 사례 보강 필요", "기술적 근거 보완"]

    return report_dict

# 실시간 대화형 면접 API
@router.post("/realtime", response_model=InterviewResponse)
async def create_realtime_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"🆕 Creating REALTIME interview session for user {current_user.id} using Resume ID: {interview_data.resume_id}")

    from utils.interview_helpers import get_candidate_info
    candidate_info = get_candidate_info(db, interview_data.resume_id)
    target_role = candidate_info.get("target_role", "일반")
    candidate_name = candidate_info.get("candidate_name", "지원자")

    new_interview = Interview(
        candidate_id=current_user.id,
        position=target_role,
        company_id=interview_data.company_id,
        resume_id=interview_data.resume_id,
        status=InterviewStatus.IN_PROGRESS,
        scheduled_time=interview_data.scheduled_time,
        start_time=get_kst_now(),
        created_at=get_kst_now()
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    db.flush() 

    logger.info(f"Realtime Interview created: ID={new_interview.id}, Candidate={candidate_name}, Target Role={target_role}")

    try:
        from utils.interview_helpers import generate_template_question, check_if_transition
        is_transition = check_if_transition(candidate_info.get("major", ""), target_role)

        try:
            if is_transition:
                from config.interview_scenario_transition import get_initial_stages
            else:
                from config.interview_scenario import get_initial_stages
            initial_stages = get_initial_stages()
        except ImportError:
            logger.warning("⚠️ Could not import interview_scenario, using hardcoded fallback questions.")
            initial_stages = [
                {"stage": "intro", "display_name": "기본 질문", "intro_sentence": "반갑습니다. 면접을 시작하기 위해 먼저 간단히 자기소개 부탁드립니다.", "template": "{candidate_name} 지원자님, 간단히 자기소개 부탁드립니다.", "order": 1},
                {"stage": "motivation", "display_name": "기본 질문", "intro_sentence": "감사합니다. 이어서 지원하신 동기에 대해 들어보고 싶습니다.", "template": "{candidate_name} 지원자님, 지원동기 말씀해주세요.", "order": 2}
            ]

        for stage_config in initial_stages:
            question_text = generate_template_question(
                stage_config.get("template", "{candidate_name}님 시작해주세요."),
                candidate_info
            )
            display_name = stage_config.get("display_name", "면접질문")
            intro_msg = stage_config.get("intro_sentence", "")
            question_text = f"{intro_msg} {question_text}" if intro_msg else question_text

            question = Question(
                content=question_text,
                category=QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.EASY,
                question_type=stage_config.get("stage", "general"),
                rubric_json={"criteria": ["명확성"]},
                position=target_role,
                created_at=get_kst_now()
            )
            db.add(question)
            db.flush()

            # Question 객체 생성 (TTS 비동기 요청 포함)
            _fire_tts_for_question(question.id, question_text)

            transcript = Transcript(
                interview_id=new_interview.id,
                speaker="AI",
                text=question_text,
                question_id=question.id,
                order=stage_config.get("order", 0),
                timestamp=get_kst_now()
            )
            db.add(transcript)

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