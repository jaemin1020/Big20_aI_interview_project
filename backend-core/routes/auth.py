from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
import logging
import requests
import os

from database import get_session
from models import User, UserCreate, UserLogin
from utils.auth_utils import get_password_hash, verify_password, create_access_token, get_current_user
from utils.common import validate_email, validate_username

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("Auth-Router")

# 회원가입
@router.post("/register")
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
@router.post("/token")  # /auth/token으로 변경됨 (기존 main.py에서는 /token)
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

# Deepgram 임시 토큰 발급 (New)
@router.get("/deepgram-token")
async def get_deepgram_token(current_user: User = Depends(get_current_user)):
    """Deepgram 사용을 위한 임시 API Key 발급"""
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    if not DEEPGRAM_API_KEY:
        raise HTTPException(status_code=500, detail="Deepgram API Key not configured on server")

    # Deepgram 프로젝트 ID는 일반적으로 키에 포함되어 있거나 필요 없을 수 있음 (임시 키 생성 API 사용)
    # Deepgram API: POST /v1/projects/{project_id}/keys
    # 프로젝트 ID를 모를 경우 'general' 스코프의 임시 키 생성 방법을 확인해야 함.
    # 대안: Deepgram SDK 사용이 권장되지만 의존성 최소화를 위해 requests 사용 시도.
    
    # Deepgram의 임시 키 생성 API는 프로젝트 ID가 필요함.
    # 프로젝트 ID를 환경변수로 관리하지 않는 경우, 
    # 차선책: 일시적으로 서버 키를 전달하지 않고, 프론트엔드가 백엔드를 Proxy로 사용하게 해야함.
    # 하지만 프론트엔드 SDK는 WSS 연결을 위해 키가 필요함.
    
    # Deepgram Console에서 Project ID 확인 필요. 
    # 없는 경우, 현재 사용 중인 Master Key를 임시 사용하도록 할 수 없으므로, 
    # 차선책으로 "On-premise" 방식인 백엔드에서 오디오 스트림을 받아 forwarding하는 것이 정석이나 구현 복잡.
    
    # 만약 Project ID를 모른다면? -> Deepgram API 키 정보 조회 API로 Project ID 획득 가능.
    
    try:
        # 멤버/프로젝트 정보 조회하여 Project ID 획득
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }
        # 프로젝트 목록 조회
        resp = requests.get("https://api.deepgram.com/v1/projects", headers=headers)
        if resp.status_code != 200:
            logger.error(f"Failed to get Deepgram projects: {resp.text}")
            raise HTTPException(status_code=500, detail="Failed to communicate with Deepgram")
            
        projects = resp.json().get("projects", [])
        if not projects:
             raise HTTPException(status_code=500, detail="No Deepgram projects found")
             
        project_id = projects[0]["project_id"]
        
        # 임시 키 생성 (TTL: 10분)
        # Deepgram Key Creation API
        create_key_url = f"https://api.deepgram.com/v1/projects/{project_id}/keys"
        payload = {
            "comment": f"Temp key for user {current_user.username}",
            "scopes": ["usage:write"], # 최소 권한
            "time_to_live_in_seconds": 600 # 10분
        }
        
        key_resp = requests.post(create_key_url, headers=headers, json=payload)
        if key_resp.status_code != 200:
            logger.error(f"Failed to create temp key: {key_resp.text}")
            raise HTTPException(status_code=500, detail="Failed to create temporary Deepgram key")
            
        temp_key = key_resp.json()["api_key"]
        return {"temp_key": temp_key}
        
    except Exception as e:
        logger.error(f"Deepgram token generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
