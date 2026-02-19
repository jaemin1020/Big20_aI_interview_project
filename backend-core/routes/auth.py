from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
import logging
import requests
import os

from database import get_session
from db_models import User, UserCreate, UserLogin
from utils.auth_utils import get_password_hash, verify_password, create_access_token, get_current_user
from utils.common import validate_email, validate_username

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("Auth-Router")

# 회원가입
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_session)):
    """회원가입

    Args:
        user_data (UserCreate): 회원가입 정보
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).

    Raises:
        HTTPException: 유효하지 않은 아이디 또는 이메일
        HTTPException: 중복된 아이디 또는 이메일

    Returns:
        dict: 회원가입 정보

    생성자: ejm
    생성일자: 2026-02-08
    """
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
        full_name=user_data.full_name,
        birth_date=user_data.birth_date,
        profile_image=user_data.profile_image
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {new_user.username} ({new_user.role})")
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}

# 로그인
@router.post("/token")  # /auth/token으로 변경됨 (기존 main.py에서는 /token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    로그인

    Args:
        form_data (OAuth2PasswordRequestForm): 로그인 정보
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).

    Returns:
        dict: 로그인 정보

    생성자: ejm
    생성일자: 2026-02-08
    """
    # 사용자 인증
    stmt = select(User).where(User.username == form_data.username)
    user = db.exec(stmt).first()
    # 비밀번호 확인
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 일치하지 않습니다."
        )
    # 토큰 생성
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}