from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlmodel import Session
from sqlalchemy.orm import attributes
from typing import Optional
import base64
import os
import json

from db_models import User
from database import get_session
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회

    생성자: ejm
    생성일자: 2026-02-06
    """
    return current_user


@router.patch("/me")
async def update_users_me(
    full_name: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    desired_company_types: Optional[str] = Form(None),  # JSON 문자열로 받음
    desired_positions: Optional[str] = Form(None),       # JSON 문자열로 받음
    profile_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    현재 로그인한 사용자 프로필 수정

    생성자: lsj
    생성일자: 2026-02-20
    """
    db_user = session.get(User, current_user.id)

    if full_name is not None:
        db_user.full_name = full_name
    if birth_date is not None:
        db_user.birth_date = birth_date
    if email is not None:
        db_user.email = email
    if phone_number is not None:
        db_user.phone_number = phone_number

    # 희망 기업 유형 (JSON 배열 문자열 → 파이썬 리스트)
    if desired_company_types is not None:
        try:
            db_user.desired_company_types = json.loads(desired_company_types)
        except Exception:
            db_user.desired_company_types = []
        # ARRAY 타입은 mutable 변경 감지가 안 되므로 명시적으로 변경됨을 표시
        attributes.flag_modified(db_user, "desired_company_types")

    # 희망 직무 (JSON 배열 문자열 → 파이썬 리스트)
    if desired_positions is not None:
        try:
            db_user.desired_positions = json.loads(desired_positions)
        except Exception:
            db_user.desired_positions = []
        # ARRAY 타입은 mutable 변경 감지가 안 되므로 명시적으로 변경됨을 표시
        attributes.flag_modified(db_user, "desired_positions")

    # profile_image 처리: 업로드된 파일을 base64로 변환하여 저장
    if profile_image is not None and profile_image.filename:
        contents = await profile_image.read()
        if len(contents) <= 5 * 1024 * 1024:
            ext = os.path.splitext(profile_image.filename)[1].lower()
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_map.get(ext, 'image/jpeg')
            b64_str = base64.b64encode(contents).decode('utf-8')
            db_user.profile_image = f"data:{mime_type};base64,{b64_str}"

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user