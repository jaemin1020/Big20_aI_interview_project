from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
<<<<<<< HEAD
import shutil
from pathlib import Path
from sqlalchemy import text
from pydantic import BaseModel

# DB 설정
from database import init_db, get_session
# DB 테이블 모듈 임포트
from models import (
    User, UserCreate, UserLogin, UserRole, Company,
    Interview, InterviewCreate, InterviewResponse, InterviewStatus,
    Question, QuestionCategory, QuestionDifficulty,
    Transcript, TranscriptCreate, Speaker,
    EvaluationReport, EvaluationReportResponse,
    Resume, ResumeChunk
)
# 인증 관련 모듈 임포트
# 인증 관련 모듈 임포트
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from utils.common import validate_email, validate_username  # 유효성 검사 추가
=======

from database import init_db
# 라우터 임포트
from routes.auth import router as auth_router
from routes.companies import router as companies_router
from routes.interviews import router as interviews_router
from routes.transcripts import router as transcripts_router
from routes.resumes import router as resumes_router
from routes.users import router as users_router
>>>>>>> 5fe6f7adb33f16443747dc01fc10ed12295552be

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backend-Core")

app = FastAPI(title="AI Interview Backend v2.0")

# DB 초기화
@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("✅ Database initialized with new schema")

# CORS 설정
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)       # /auth
app.include_router(companies_router)  # /companies
app.include_router(interviews_router) # /interviews
app.include_router(transcripts_router)# /transcripts
app.include_router(resumes_router)    # /api/resumes
app.include_router(users_router)      # /users

<<<<<<< HEAD
# Celery 설정
celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# ==================== Auth Endpoints ====================
# 회원가입
@app.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_session)):
    # 1. 유효성 검사 (길이 및 포맷)
    if not validate_username(user_data.username):
        raise HTTPException(
            status_code=400, 
            detail="아이디는 4~12자의 영문 소문자, 숫자, 밑줄(_)만 사용 가능합니다."
        )
    
    if not validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="유효하지 않은 이메일 형식입니다.")

    # 2. 중복 확인
    stmt = select(User).where(
        (User.username == user_data.username) | (User.email == user_data.email)
    )
    existing_user = db.exec(stmt).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # 새 사용자 생성
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        role=user_data.role,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username} ({new_user.role})")
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}

# 로그인
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    # 사용자 인증
    stmt = select(User).where(User.username == form_data.username)
    user = db.exec(stmt).first()
    # 비밀번호 확인
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    # 토큰 생성
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

# 사용자 정보 조회
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== Interview Endpoints ====================
# 면접 생성
@app.post("/interviews", response_model=InterviewResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접 세션 생성 및 질문 생성"""
    
    # 1. Interview 레코드 생성 (상태: SCHEDULED)
    new_interview = Interview(
        candidate_id=current_user.id,
        position=interview_data.position,
        company_id=interview_data.company_id,
        status=InterviewStatus.SCHEDULED,
        scheduled_time=interview_data.scheduled_time,
        start_time=datetime.utcnow()
    )
    # DB에 저장
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    
    logger.info(f"Interview created: ID={new_interview.id}, Position={new_interview.position}")
    
    # 2. AI 질문 생성
    # Backend가 직접 LLM을 돌리지 않으므로, Celery Task를 호출합니다.
    generated_questions = []
    
    try:
        logger.info("Requesting question generation from AI-Worker...")
        # Celery 태스크 호출 (최대 90초 대기 - 모델 로딩 시간 고려)
        task = celery_app.send_task(
            "tasks.question_generator.generate_questions",
            args=[interview_data.position, new_interview.id, 5]
        )
        # 동기적으로 결과를 기다림 (UX상 질문이 바로 필요함)
        generated_questions = task.get(timeout=180)
        logger.info(f"Received {len(generated_questions)} questions from AI-Worker")
        
    except Exception as e:
        logger.warning(f"AI-Worker question generation failed ({e}). Using fallback questions.")
        # 실패 시 폴백 질문 생성
        generated_questions = [
            f"{interview_data.position} 직무에 지원하게 된 동기를 구체적으로 말씀해주세요.",
            "가장 도전적이었던 프로젝트 경험과 그 과정에서 얻은 교훈은 무엇인가요?",
            f"{interview_data.position}로서 본인의 가장 큰 강점과 보완하고 싶은 점은 무엇인가요?",
            "갈등 상황을 해결했던 구체적인 사례가 있다면 설명해주세요.",
            "향후 5년 뒤의 커리어 목표는 무엇인가요?"
        ]

    # 3. Questions 및 Transcript 테이블에 저장
    try:
        for i, q_text in enumerate(generated_questions):
            # 3-1. 질문 은행에 저장
            question = Question(
                content=q_text,
                category=QuestionCategory.TECHNICAL if i < 3 else QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.MEDIUM,
                rubric_json={
                    "criteria": ["구체성", "직무 적합성", "논리력"], 
                    "weight": {"content": 0.5, "communication": 0.5}
                },
                position=interview_data.position
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            
            # 3-2. Transcript에 AI 발화로 기록
            transcript = Transcript(
                interview_id=new_interview.id,
                speaker=Speaker.AI,
                text=q_text,
                question_id=question.id,
                order=i
            )
            db.add(transcript)
        
        # 면접 상태 업데이트: LIVE
        new_interview.status = InterviewStatus.LIVE
        db.add(new_interview)
        db.commit()
        db.refresh(new_interview)
        
    except Exception as e:
        logger.error(f"Failed to save questions: {e}")
        # 에러 발생 시에도 면접 세션은 반환 (빈 질문 목록일 수 있음)
    
    return InterviewResponse(
        id=new_interview.id,
        candidate_id=new_interview.candidate_id,
        position=new_interview.position,
        status=new_interview.status,
        start_time=new_interview.start_time,
        end_time=new_interview.end_time,
        overall_score=new_interview.overall_score
    )

# ==================== Question Endpoints ====================

# 면접 질문 조회
@app.get("/interviews/{interview_id}/questions")
async def get_interview_questions(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접의 질문 목록 조회 (Transcript에서 AI 발화만 필터링)"""
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id,
        Transcript.speaker == Speaker.AI
    ).order_by(Transcript.order)
    
    transcripts = db.exec(stmt).all()
    
    return [
        {
            "id": t.question_id,
            "content": t.text,
            "order": t.order,
            "timestamp": t.timestamp
        }
        for t in transcripts
    ]

# ==================== Transcript Endpoints ====================

# 대화 기록 저장
@app.post("/transcripts")
async def create_transcript(
    transcript_data: TranscriptCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """실시간 대화 기록 저장 (STT 결과)"""
    
    transcript = Transcript(
        interview_id=transcript_data.interview_id,
        speaker=transcript_data.speaker,
        text=transcript_data.text,
        question_id=transcript_data.question_id
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    logger.info(f"Transcript saved: Interview={transcript.interview_id}, Speaker={transcript.speaker}")
    
    # 사용자 답변인 경우 AI 평가 요청
    if transcript.speaker == Speaker.USER:
        # 해당 질문 조회
        question = db.get(Question, transcript.question_id)
        if question:
            celery_app.send_task(
                "tasks.evaluator.analyze_answer",
                args=[
                    transcript.id,
                    question.content,
                    transcript.text,
                    question.rubric_json,
                    question.id  # 질문 ID 추가 (평균 점수 업데이트용)
                ]
            )
            logger.info(f"Evaluation task sent for transcript {transcript.id}")
    
    return {"id": transcript.id, "status": "saved"}

# 대화 기록 조회
@app.get("/interviews/{interview_id}/transcripts")
async def get_interview_transcripts(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접의 전체 대화 기록 조회"""
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

# ==================== Evaluation Endpoints ====================

# 면접 완료 처리 및 최종 평가 리포트 생성
@app.post("/interviews/{interview_id}/complete")
async def complete_interview(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접 종료 및 최종 평가 리포트 생성"""
    
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # 면접 종료 처리
    interview.status = InterviewStatus.COMPLETED
    interview.end_time = datetime.utcnow()
    db.add(interview)
    db.commit()
    
    # 평가 리포트 생성 태스크 전달
    celery_app.send_task(
        "tasks.evaluator.generate_final_report",
        args=[interview_id]
    )
    
    logger.info(f"Interview {interview_id} completed. Report generation started.")
    return {"status": "completed", "interview_id": interview_id}

@app.get("/interviews/{interview_id}/report", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """평가 리포트 조회"""
    stmt = select(EvaluationReport).where(
        EvaluationReport.interview_id == interview_id
    )
    report = db.exec(stmt).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet available")
    
    return report

# ==================== Resume Endpoints ====================

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("./uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """이력서 파일 업로드 (PDF, DOC, DOCX)"""
    
    # 파일 확장자 검증
    allowed_extensions = [".pdf", ".doc", ".docx"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # 파일 저장 경로 생성 (candidate_id_timestamp_filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # 파일 저장
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Resume 레코드 생성
        new_resume = Resume(
            candidate_id=current_user.id,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            processing_status="pending"
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        
        logger.info(f"Resume uploaded: ID={new_resume.id}, User={current_user.username}, File={file.filename}")
        
        # Celery 태스크로 이력서 파싱 및 구조화 작업 전달
        celery_app.send_task(
            "parse_resume_pdf",
            args=[new_resume.id, str(file_path)]
        )
        logger.info(f"Resume parsing task sent for ID={new_resume.id}")
        
        return {
            "id": new_resume.id,
            "file_name": new_resume.file_name,
            "file_size": new_resume.file_size,
            "status": "uploaded",
            "message": "Resume uploaded successfully. Processing will begin shortly."
        }
        
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        # 실패 시 파일 삭제
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="File upload failed")


# 🧪 테스트용 엔드포인트들 (인증 불필요)
# 주의: 구체적인 경로를 먼저 정의해야 FastAPI 라우팅이 제대로 작동함

# 🧪 테스트용: 인증 없는 이력서 상태 조회
@app.get("/test/resumes/{resume_id}")
async def test_get_resume_status(
    resume_id: int,
    db: Session = Depends(get_session)
):
    """
    테스트용 이력서 상태 조회 (인증 불필요)
    
    - 임베딩 처리 상태 및 청크 정보 확인
    """
    return {"message": "Endpoint is ALIVE", "id": resume_id}


# 🧪 테스트용: 인증 없는 이력서 업로드 (개발/디버깅용)
@app.post("/test/upload-resume")
async def test_upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_session)
):
    """
    테스트용 이력서 업로드 (인증 불필요)
    
    - 개발 및 디버깅 목적으로만 사용
    - 임베딩 처리 결과를 바로 확인 가능
    """
    # 파일 검증
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF, DOC, DOCX files are allowed")
    
    # 테스트 사용자가 없으면 자동 생성
    from sqlmodel import select
    stmt = select(User).where(User.username == "test_user")
    test_user = db.exec(stmt).first()
    
    if not test_user:
        from auth import get_password_hash
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash=get_password_hash("test1234"),
            full_name="테스트 사용자",
            role=UserRole.CANDIDATE
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        logger.info(f"✅ 테스트용 더미 사용자 생성 완료 (ID: {test_user.id})")
    
    test_user_id = test_user.id
    
    try:
        # 파일 저장
        upload_dir = Path("./uploads/resumes")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        with file_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_size = file_path.stat().st_size
        
        # Resume 레코드 생성
        resume = Resume(
            candidate_id=test_user_id,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            processing_status="pending"
        )
        
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        logger.info(f"✅ [TEST] Resume uploaded: {resume.id} by test_user")
        
        # Celery Task 전송 (ai-worker로 전달)
        task = celery_app.send_task(
            "parse_resume_pdf",  # Worker에 등록된 task 이름
            args=[resume.id, str(file_path)]
        )
        
        return {
            "message": "✅ 테스트 업로드 성공! 임베딩 처리 중...",
            "resume_id": resume.id,
            "file_name": file.filename,
            "file_size": file_size,
            "task_id": task.id,
            "status_check_url": f"/test/resumes/{resume.id}",
            "note": "⚠️ 이 엔드포인트는 테스트용입니다. 운영 환경에서는 /resumes/upload를 사용하세요."
        }
        
    except Exception as e:
        logger.error(f"Test resume upload failed: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# 🧪 테스트용: 인증 없는 이력서 검색
@app.post("/test/resumes/search")
async def test_search_resumes(
    query: str,
    top_k: int = 10,
    min_score: float = 0.5,
    db: Session = Depends(get_session)
):
    """
    테스트용 이력서 검색 (인증 불필요)
    
    Args:
        query: 검색 쿼리 (예: "Python 백엔드 개발자")
        top_k: 반환할 최대 결과 수 (기본: 10)
        min_score: 최소 유사도 점수 (0~1, 기본: 0.5)
    """
    logger.info(f"🔍 [TEST] Resume search: query='{query}', top_k={top_k}")
    
    try:
        # 1. 쿼리를 임베딩으로 변환 (Celery Task 사용)
        task = celery_app.send_task(
            "generate_query_embedding",
            args=[query]
        )
        
        # 결과 대기 (최대 10초)
        query_embedding = task.get(timeout=10)
        logger.info(f"✅ Query embedding generated (dim: {len(query_embedding)})")
        
    except Exception as e:
        logger.error(f"❌ Failed to generate query embedding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}"
        )
    
    # 2. pgvector로 유사도 검색
    sql_query = text("""
        SELECT 
            rc.id as chunk_id,
            rc.resume_id,
            rc.content,
            rc.chunk_index,
            1 - (rc.embedding <=> CAST(:query_embedding AS vector)) as similarity_score,
            r.file_name,
            r.candidate_id,
            u.full_name as candidate_name,
            u.email as candidate_email
        FROM resume_chunks rc
        JOIN resumes r ON rc.resume_id = r.id
        JOIN users u ON r.candidate_id = u.id
        WHERE 
            r.processing_status = 'completed'
            AND rc.embedding IS NOT NULL
            AND 1 - (rc.embedding <=> CAST(:query_embedding AS vector)) >= :min_score
        ORDER BY rc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
    """)
    
    try:
        result = db.execute(
            sql_query,
            {
                "query_embedding": str(query_embedding),
                "min_score": min_score,
                "top_k": top_k
            }
        )
        
        chunks = result.fetchall()
        logger.info(f"📊 Found {len(chunks)} matching chunks")
        
    except Exception as e:
        logger.error(f"❌ Database search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    # 3. Resume별로 그룹화 (중복 제거)
    resume_map = {}
    for chunk in chunks:
        resume_id = chunk.resume_id
        
        if resume_id not in resume_map:
            resume_map[resume_id] = {
                "resume_id": resume_id,
                "file_name": chunk.file_name,
                "candidate_name": chunk.candidate_name,
                "candidate_email": chunk.candidate_email,
                "max_similarity": float(chunk.similarity_score),
                "matched_chunks": []
            }
        
        resume_map[resume_id]["matched_chunks"].append({
            "chunk_index": chunk.chunk_index,
            "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "similarity_score": float(chunk.similarity_score)
        })
        
        # 최고 유사도 업데이트
        if chunk.similarity_score > resume_map[resume_id]["max_similarity"]:
            resume_map[resume_id]["max_similarity"] = float(chunk.similarity_score)
    
    # 4. 유사도 순으로 정렬
    results = sorted(
        resume_map.values(),
        key=lambda x: x["max_similarity"],
        reverse=True
    )
    
    logger.info(f"✅ [TEST] Found {len(results)} resumes matching query")
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results,
        "note": "⚠️ 이 엔드포인트는 테스트용입니다."
    }




# 이력서 상태 조회 (단일)
@app.get("/resumes/{resume_id}")
async def get_resume_status(
    resume_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """이력서 처리 상태 및 정보 조회"""
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # 권한 확인: 본인 또는 recruiter/admin만 조회 가능
    if resume.candidate_id != current_user.id and current_user.role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    logger.info(f"Resume {resume_id} status requested by {current_user.username}")
    
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_size": resume.file_size,
        "processing_status": resume.processing_status,
        "uploaded_at": resume.uploaded_at,
        "processed_at": resume.processed_at,
        "has_embedding": resume.embedding is not None,
        "has_structured_data": resume.structured_data is not None,
        "structured_data": resume.structured_data if resume.structured_data else {}
    }

# 이력서 목록 조회
@app.get("/resumes")
async def get_user_resumes(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """현재 사용자의 이력서 목록 조회"""
    stmt = select(Resume).where(
        Resume.candidate_id == current_user.id
    ).order_by(Resume.uploaded_at.desc())
    
    resumes = db.exec(stmt).all()
    
    logger.info(f"Resume list requested by {current_user.username}: {len(resumes)} resumes")
    
    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "file_size": r.file_size,
            "processing_status": r.processing_status,
            "uploaded_at": r.uploaded_at,
            "processed_at": r.processed_at,
            "has_embedding": r.embedding is not None
        }
        for r in resumes
    ]


# ==================== Resume Search Endpoints (Phase 2) ====================

class ResumeSearchRequest(BaseModel):
    """이력서 검색 요청"""
    query: str
    top_k: int = 10
    min_score: float = 0.5


@app.post("/resumes/search")
async def search_resumes(
    request: ResumeSearchRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    벡터 유사도 기반 이력서 검색
    
    Args:
        query: 검색 쿼리 (예: "Python 백엔드 개발자")
        top_k: 반환할 최대 결과 수 (기본: 10)
        min_score: 최소 유사도 점수 (0~1, 기본: 0.5)
        
    Returns:
        검색 결과 리스트 (유사도 순 정렬)
    """
    logger.info(f"🔍 Resume search: query='{request.query}', top_k={request.top_k}, user={current_user.id}")
    
    try:
        # 1. 쿼리를 임베딩으로 변환 (Celery Task 사용)
        task = celery_app.send_task(
            "generate_query_embedding",
            args=[request.query]
        )
        
        # 결과 대기 (최대 10초)
        query_embedding = task.get(timeout=10)
        logger.info(f"✅ Query embedding generated (dim: {len(query_embedding)})")
        
    except Exception as e:
        logger.error(f"❌ Failed to generate query embedding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}"
        )
    
    # 2. pgvector로 유사도 검색
    # <=> 연산자: 코사인 거리 (0에 가까울수록 유사)
    # 1 - 코사인 거리 = 코사인 유사도
    sql_query = text("""
        SELECT 
            rc.id as chunk_id,
            rc.resume_id,
            rc.content,
            rc.chunk_index,
            1 - (rc.embedding <=> CAST(:query_embedding AS vector)) as similarity_score,
            r.file_name,
            r.candidate_id,
            u.full_name as candidate_name,
            u.email as candidate_email
        FROM resume_chunks rc
        JOIN resumes r ON rc.resume_id = r.id
        JOIN users u ON r.candidate_id = u.id
        WHERE 
            r.processing_status = 'completed'
            AND rc.embedding IS NOT NULL
            AND 1 - (rc.embedding <=> CAST(:query_embedding AS vector)) >= :min_score
        ORDER BY rc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
    """)
    
    try:
        result = db.execute(
            sql_query,
            {
                "query_embedding": str(query_embedding),
                "min_score": request.min_score,
                "top_k": request.top_k
            }
        )
        
        chunks = result.fetchall()
        logger.info(f"📊 Found {len(chunks)} matching chunks")
        
    except Exception as e:
        logger.error(f"❌ Database search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    # 3. Resume별로 그룹화 (중복 제거)
    resume_map = {}
    for chunk in chunks:
        resume_id = chunk.resume_id
        
        if resume_id not in resume_map:
            resume_map[resume_id] = {
                "resume_id": resume_id,
                "file_name": chunk.file_name,
                "candidate_name": chunk.candidate_name,
                "candidate_email": chunk.candidate_email,
                "max_similarity": float(chunk.similarity_score),
                "matched_chunks": []
            }
        
        resume_map[resume_id]["matched_chunks"].append({
            "chunk_index": chunk.chunk_index,
            "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "similarity_score": float(chunk.similarity_score)
        })
        
        # 최고 유사도 업데이트
        if chunk.similarity_score > resume_map[resume_id]["max_similarity"]:
            resume_map[resume_id]["max_similarity"] = float(chunk.similarity_score)
    
    # 4. 유사도 순으로 정렬
    results = sorted(
        resume_map.values(),
        key=lambda x: x["max_similarity"],
        reverse=True
    )
    
    logger.info(f"✅ Found {len(results)} resumes matching query")
    
    return {
        "query": request.query,
        "total_results": len(results),
        "results": results
    }


# ==================== Interview Context & RAG Search (Phase 2) ====================

@app.get("/interviews/{interview_id}/context")
async def get_interview_context(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    면접 컨텍스트 로드 (Phase 2: RAG 질문 생성용)
    
    Returns:
        - company_id, company_name, company_ideal
        - position (지원 직무)
        - resume_id
    """
    logger.info(f"🎯 [Interview {interview_id}] 컨텍스트 로드 요청")
    
    # 1. Interview 조회
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # 권한 체크
    if interview.candidate_id != current_user.id and current_user.role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 2. Company 정보 조회
    company_data = None
    if interview.company_id:
        company = db.get(Company, interview.company_id)
        if company:
            company_data = {
                "company_id": company.id,
                "company_name": company.company_name,
                "company_ideal": company.ideal,
                "company_description": company.description
            }
    
    # 3. Resume 정보 조회
    resume_data = None
    if interview.resume_id:
        resume = db.get(Resume, interview.resume_id)
        if resume:
            resume_data = {
                "resume_id": resume.id,
                "file_name": resume.file_name,
                "processing_status": resume.processing_status
            }
    
    context = {
        "interview_id": interview.id,
        "position": interview.position,
        "company": company_data,
        "resume": resume_data,
        "status": interview.status
    }
    
    logger.info(f"✅ [Interview {interview_id}] 컨텍스트 로드 완료")
    return context


class HybridSearchRequest(BaseModel):
    """하이브리드 검색 요청 (Phase 2)"""
    interview_id: int
    section_type: str  # 'skill_cert', 'career_project', 'cover_letter'
    query: str
    top_k: int = 5
    min_score: float = 0.5


@app.post("/search/hybrid")
async def hybrid_search(
    request: HybridSearchRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    하이브리드 검색 (Phase 2: 섹션 + 회사 + 직무 필터링)
    
    검색 전략:
    1. Interview에서 company_id, position 가져오기
    2. ResumeChunk에서 section_type으로 필터링
    3. 벡터 유사도 검색
    4. 결과 반환
    """
    logger.info(f"🔍 [Hybrid Search] Interview={request.interview_id}, Section={request.section_type}, Query='{request.query}'")
    
    # 1. Interview 정보 조회
    interview = db.get(Interview, request.interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # 권한 체크
    if interview.candidate_id != current_user.id and current_user.role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 2. 쿼리 임베딩 생성
    try:
        task = celery_app.send_task(
            "generate_query_embedding",
            args=[request.query]
        )
        query_embedding = task.get(timeout=10)
        logger.info(f"✅ Query embedding generated (dim: {len(query_embedding)})")
    except Exception as e:
        logger.error(f"❌ Failed to generate query embedding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}"
        )
    
    # 3. 하이브리드 검색 (섹션 타입 필터링)
    sql_query = text("""
        SELECT 
            rc.id as chunk_id,
            rc.resume_id,
            rc.content,
            rc.chunk_index,
            rc.section_type,
            1 - (rc.embedding <=> CAST(:query_embedding AS vector)) as similarity_score,
            r.file_name
        FROM resume_chunks rc
        JOIN resumes r ON rc.resume_id = r.id
        WHERE 
            r.id = :resume_id
            AND r.processing_status = 'completed'
            AND rc.embedding IS NOT NULL
            AND rc.section_type = :section_type
            AND 1 - (rc.embedding <=> CAST(:query_embedding AS vector)) >= :min_score
        ORDER BY rc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
    """)
    
    try:
        result = db.execute(
            sql_query,
            {
                "resume_id": interview.resume_id,
                "section_type": request.section_type,
                "query_embedding": str(query_embedding),
                "min_score": request.min_score,
                "top_k": request.top_k
            }
        )
        
        chunks = result.fetchall()
        logger.info(f"📊 Found {len(chunks)} matching chunks (section={request.section_type})")
        
    except Exception as e:
        logger.error(f"❌ Hybrid search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    # 4. 결과 포맷팅
    results = [
        {
            "chunk_id": chunk.chunk_id,
            "content": chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content,
            "section_type": chunk.section_type,
            "similarity_score": float(chunk.similarity_score)
        }
        for chunk in chunks
    ]
    
    logger.info(f"✅ [Hybrid Search] Returned {len(results)} results")
    
    return {
        "interview_id": request.interview_id,
        "section_type": request.section_type,
        "query": request.query,
        "total_results": len(results),
        "results": results
    }


# ==================== Recruiter Endpoints ====================

# 전체 인터뷰 목록 조회
@app.get("/interviews")
async def get_all_interviews(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """전체 인터뷰 목록 조회 (리크루터용)"""
    
    # 권한 체크: recruiter 또는 admin만 접근 가능
    if current_user.role not in ["recruiter", "admin"]:
        # candidate는 자신의 인터뷰만 조회 가능
        stmt = select(Interview).where(
            Interview.candidate_id == current_user.id
        ).order_by(Interview.created_at.desc())
    else:
        # recruiter/admin은 전체 조회
        stmt = select(Interview).order_by(Interview.created_at.desc())
    
    interviews = db.exec(stmt).all()
    
    # 응답 데이터 구성 (candidate 정보 포함)
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
    
    logger.info(f"Interviews list requested by {current_user.username} ({current_user.role}): {len(result)} records")
    return result

# ==================== Health Check ====================

# 서버 상태 확인
=======
# Health Check
>>>>>>> 5fe6f7adb33f16443747dc01fc10ed12295552be
@app.get("/")
async def root():
    return {
        "service": "AI Interview Backend v2.0",
        "status": "running",
        "doc": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)