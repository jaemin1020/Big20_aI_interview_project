from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import Session
from utils.auth_utils import get_current_user
from models import User
from database import get_session
import os
import logging
from typing import Optional
import asyncio

logger = logging.getLogger("STT-Service")

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])

# Deepgram API 키는 서버 환경 변수에서만 관리
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

@router.post("/token")
async def get_deepgram_token(current_user: User = Depends(get_current_user)):
    """
    Deepgram 임시 토큰 생성 (클라이언트용)
    
    보안상 실제 API 키는 노출하지 않고, 
    제한된 권한의 임시 토큰을 발급합니다.
    """
    if not DEEPGRAM_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Deepgram API key not configured on server"
        )
    
    # TODO: Deepgram의 임시 토큰 생성 API 사용
    # 현재는 직접 키를 반환하지만, 프로덕션에서는 
    # Deepgram의 Key Management API를 사용하여 
    # 시간 제한이 있는 임시 키를 생성해야 합니다.
    
    logger.warning("⚠️ Using direct API key. Implement temporary token generation for production.")
    
    return {
        "api_key": DEEPGRAM_API_KEY,
        "expires_in": 3600,  # 1시간
        "message": "Use this key for Deepgram connection"
    }

@router.websocket("/ws/{interview_id}")
async def deepgram_proxy_websocket(
    websocket: WebSocket,
    interview_id: int
):
    """
    Deepgram WebSocket 프록시
    
    클라이언트 -> 백엔드 -> Deepgram 구조로 
    오디오 스트림을 중계하여 API 키를 보호합니다.
    """
    await websocket.accept()
    
    if not DEEPGRAM_API_KEY:
        await websocket.send_json({
            "type": "error",
            "message": "Deepgram API key not configured"
        })
        await websocket.close()
        return
    
    try:
        # Deepgram WebSocket 연결 설정
        from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
        
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        dg_connection = deepgram.listen.websocket.v("1")
        
        # Deepgram 이벤트 핸들러
        def on_message(self, result, **kwargs):
            # Deepgram 결과를 클라이언트로 전달
            asyncio.create_task(websocket.send_json({
                "type": "transcript",
                "data": result
            }))
        
        def on_error(self, error, **kwargs):
            logger.error(f"Deepgram error: {error}")
            asyncio.create_task(websocket.send_json({
                "type": "error",
                "message": str(error)
            }))
        
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        
        # Deepgram 연결 시작
        options = LiveOptions(
            model="nova-2",
            language="ko",
            smart_format=True,
            encoding="linear16",
            sample_rate=16000
        )
        
        if not dg_connection.start(options):
            raise Exception("Failed to start Deepgram connection")
        
        logger.info(f"Deepgram proxy started for interview {interview_id}")
        
        # 클라이언트로부터 오디오 데이터 수신 및 Deepgram으로 전달
        while True:
            data = await websocket.receive_bytes()
            dg_connection.send(data)
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from interview {interview_id}")
    except Exception as e:
        logger.error(f"Deepgram proxy error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"STT service error: {str(e)}"
        })
    finally:
        if 'dg_connection' in locals():
            dg_connection.finish()
        await websocket.close()
