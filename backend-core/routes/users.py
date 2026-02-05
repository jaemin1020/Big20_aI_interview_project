from fastapi import APIRouter, Depends
from models import User
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return current_user
