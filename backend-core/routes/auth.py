from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime
import logging

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

    - 탈퇴한 계정과 동일 아이디/이메일이면 회원가입 허용 (활성 계정만 중복 검사)

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

    # 2. 중복 확인 - 활성(비탈퇴) 계정만 대상으로 검사
    stmt = select(User).where(
        ((User.username == user_data.username) | (User.email == user_data.email))
        & (User.is_withdrawn == False)  # noqa: E712
    )
    existing_user = db.exec(stmt).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디 또는 이메일입니다.")

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

    logger.info("New user registered: %s (%s)", new_user.username, new_user.role)
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}


# 로그인
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    로그인 - 탈퇴한 계정은 로그인 차단

    생성자: ejm
    생성일자: 2026-02-08
    """
    # 활성 계정 중에서만 조회
    stmt = select(User).where(
        (User.username == form_data.username) & (User.is_withdrawn == False)  # noqa: E712
    )
    user = db.exec(stmt).first()

    # 비밀번호 확인
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 일치하지 않습니다."
        )

    # 토큰 생성
    access_token = create_access_token(data={"sub": user.username})
    logger.info("User logged in: %s", user.username)
    return {"access_token": access_token, "token_type": "bearer"}


# 비밀번호 변경
@router.patch("/password")
async def change_password(
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """비밀번호 변경"""
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 최소 8자 이상이어야 합니다.")

    db_user = db.get(User, current_user.id)
    db_user.password_hash = get_password_hash(new_password)
    db.add(db_user)
    db.commit()
    logger.info("Password changed: %s", current_user.username)
    return {"message": "비밀번호가 변경되었습니다."}


# 회원 탈퇴
@router.delete("/withdraw")
async def withdraw(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    회원 탈퇴 (soft delete)
    - DB에는 기록 보존
    - is_withdrawn=True, withdrawn_at=현재시각 설정
    - 이후 동일 아이디/이메일로 재가입 가능

    생성자: lsj
    생성일자: 2026-02-20
    """
    db_user = db.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    db_user.is_withdrawn = True
    db_user.withdrawn_at = datetime.now()
    db.add(db_user)
    db.commit()

    logger.info("User withdrawn: %s (id=%s)", current_user.username, current_user.id)
    return {"message": "회원 탈퇴가 완료되었습니다."}
