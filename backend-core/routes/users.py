from fastapi import APIRouter, Depends
<<<<<<< HEAD
from db_models import User
=======
from models import User
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    
    Args:
        current_user (User): 현재 사용자
        
    Returns:
        dict: 사용자 정보
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    return current_user
