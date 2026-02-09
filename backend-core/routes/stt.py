from fastapi import APIRouter, UploadFile, File, HTTPException, status, WebSocket
from celery import Celery
import os
import logging
import base64
import json
import asyncio

logger = logging.getLogger("STT-Service")

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])

# Celery 설정
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/0")
celery_app = Celery("ai_worker", broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)


@router.post("/recognize")
async def recognize_audio(file: UploadFile = File(...)):
    """
    오디오 파일을 AI-Worker로 전송하여 STT 수행
    
    Args:
        file (UploadFile): 오디오 파일
        
    Returns:
        dict: STT 결과
    """
    try:
        # 파일 읽기
        audio_content = await file.read()
        
        # Base64 인코딩 (Celery JSON Serialization 호환)
        audio_b64 = base64.b64encode(audio_content).decode('utf-8')
        
        # AI-Worker에 작업 요청
        logger.info(f"Sending STT task to AI-Worker (size: {len(audio_content)} bytes)")
        task = celery_app.send_task(
            "tasks.stt.recognize",
            args=[audio_b64]
        )
        
        # 결과 대기 (최대 60초)
        # 중요: task.get()은 Blocking I/O이므로 메인 이벤트 루프를 차단하지 않도록 별도 스레드에서 실행
        # 모델 초기 로딩 시간을 고려하여 타임아웃을 넉넉하게 설정 (60s -> 300s)
        result = await asyncio.to_thread(task.get, timeout=300)
        
        if isinstance(result, dict) and result.get("status") == "error":
            error_msg = result.get("message", "Unknown error from worker")
            logger.error(f"Worker report error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Worker Error: {error_msg}"
            )
            
        text = result.get("text", "")
        logger.info(f"STT Recognition Success: {len(text)} chars")
        return {"text": text}
        
    except Exception as e:
        logger.error(f"STT Error: {str(e)}", exc_info=True)
        # 타임아웃 등
        detail_msg = f"STT processing failed: {str(e)}"
        if "Timeout" in str(e):
             detail_msg = "STT Service Timeout (Network or Worker busy)"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg
        )


@router.websocket("/ws/{interview_id}")
async def stt_websocket(websocket: WebSocket, interview_id: int):
    """
    [Deprecated] WebSocket STT Endpoint
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "error",
        "message": "WebSocket STT is deprecated. Please use POST /stt/recognize."
    })
    await websocket.close()

