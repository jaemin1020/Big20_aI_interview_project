
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from database import get_session
from db_models import User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_password(plain_password, hashed_password):
    """설명:
        평문 비밀번호와 해시된 비밀번호를 bcrypt로 비교 확인.

    Args:
        plain_password (str): 사용자가 입력한 평문 비밀번호.
        hashed_password (str): DB에 저장된 bcrypt 해시값.

    Returns:
        bool: 일치하면 True, 아니면 False.

    생성자: ejm
    생성일자: 2026-02-04
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """설명:
        평문 비밀번호를 bcrypt 해시값으로 변환.

    Args:
        password (str): 해시할 평문 비밀번호.

    Returns:
        str: bcrypt 해시된 비밀번호.

    생성자: ejm
    생성일자: 2026-02-04
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """설명:
        주어진 데이터를 포함한 JWT 액세스 토큰을 생성.

    Args:
        data (dict): 토큰에 포함할 페이로드 (예: {"sub": username}).
        expires_delta (Optional[timedelta]): 토큰 유효 시간. None이면 환경변수 기본값 사용.

    Returns:
        str: 서명된 JWT 액세스 토큰 문자열.

    생성자: ejm
    생성일자: 2026-02-04
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    """설명:
        Bearer 토큰을 디코딩하여 현재 로그인한 사용자를 DB에서 조회.
        토큰 검증 실패 또는 관련 사용자가 없으면 401 예외를 발생시킴.

    Args:
        token (str): Authorization 헤더의 Bearer 토큰.
        db (Session): DB 세션 의존성 주입.

    Returns:
        User: 인증된 사용자 객체.

    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자가 없는 경우 (401).

    생성자: ejm
    생성일자: 2026-02-04
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    statement = select(User).where(
        (User.username == username) & (User.is_withdrawn.is_(False))
    )
    user = db.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user
