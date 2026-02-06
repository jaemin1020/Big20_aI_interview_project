"""
이력서 업로드 및 관리 API
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlmodel import Session, select
from models import Resume, User
from database import get_session
from utils.auth_utils import get_current_user
from celery import Celery
import os
import shutil
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger("ResumeAPI")

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

# Celery 앱 (환경변수에서 설정)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

# 업로드 디렉토리
UPLOAD_DIR = os.getenv("RESUME_UPLOAD_DIR", "./uploads/resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    이력서 PDF 업로드
    
    - 파일 저장
    - DB 레코드 생성
    - 비동기 파싱 작업 전송
    """
    # 파일 확장자 검증
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드 가능합니다."
        )
    
    # 파일 크기 검증 (10MB 제한)
    file.file.seek(0, 2)  # 파일 끝으로 이동
    file_size = file.file.tell()
    file.file.seek(0)  # 파일 처음으로 복귀
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기는 10MB 이하여야 합니다."
        )
    
    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"파일 저장 완료: {file_path}")
    except Exception as e:
        logger.error(f"파일 저장 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 저장 중 오류가 발생했습니다."
        )
    
    # DB 레코드 생성
    resume = Resume(
        candidate_id=user.id,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        processing_status="pending"
    )
    
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    logger.info(f"Resume {resume.id} 생성 완료")
    
    # 비동기 파싱 작업 전송 (Celery)
    try:
        celery_app.send_task(
            "parse_resume_pdf",
            args=[resume.id, file_path]
        )
        logger.info(f"Resume {resume.id} 파싱 작업 전송 완료")
    except Exception as e:
        logger.error(f"Celery 작업 전송 실패: {e}")
        # 실패해도 레코드는 생성됨 (나중에 재처리 가능)
    
    return {
        "resume_id": resume.id,
        "file_name": file.filename,
        "file_size": file_size,
        "status": "processing",
        "message": "이력서 업로드 완료. 파싱 중입니다."
    }


@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """이력서 조회"""
    resume = db.get(Resume, resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이력서를 찾을 수 없습니다."
        )
    
    # 권한 확인 (본인 또는 관리자만)
    if resume.candidate_id != user.id and user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_size": resume.file_size,
        "uploaded_at": resume.uploaded_at,
        "processed_at": resume.processed_at,
        "processing_status": resume.processing_status,
        "has_structured_data": resume.structured_data is not None,
        "structured_data": resume.structured_data if resume.processing_status == "completed" else None
    }


@router.get("/user/{user_id}")
async def get_user_resumes(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """사용자의 이력서 목록 조회"""
    # 권한 확인
    if user_id != user.id and user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    stmt = select(Resume).where(
        Resume.candidate_id == user_id,
        Resume.is_active == True
    ).order_by(Resume.uploaded_at.desc())
    
    resumes = db.exec(stmt).all()
    
    return {
        "user_id": user_id,
        "total": len(resumes),
        "resumes": [
            {
                "id": r.id,
                "file_name": r.file_name,
                "uploaded_at": r.uploaded_at,
                "processing_status": r.processing_status
            }
            for r in resumes
        ]
    }


@router.post("/{resume_id}/reprocess")
async def reprocess_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """이력서 재처리"""
    resume = db.get(Resume, resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이력서를 찾을 수 없습니다."
        )
    
    # 권한 확인
    if resume.candidate_id != user.id and user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    # 재처리 작업 전송
    try:
        celery_app.send_task(
            "reprocess_resume",
            args=[resume_id]
        )
        
        # 상태 업데이트
        resume.processing_status = "pending"
        db.add(resume)
        db.commit()
        
        return {
            "resume_id": resume_id,
            "status": "pending",
            "message": "재처리 작업이 시작되었습니다."
        }
    except Exception as e:
        logger.error(f"재처리 작업 전송 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="재처리 작업 전송 중 오류가 발생했습니다."
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """이력서 삭제 (soft delete)"""
    resume = db.get(Resume, resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이력서를 찾을 수 없습니다."
        )
    
    # 권한 확인
    if resume.candidate_id != user.id and user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    # Soft delete
    resume.is_active = False
    db.add(resume)
    db.commit()
    
    return {
        "resume_id": resume_id,
        "message": "이력서가 삭제되었습니다."
    }
