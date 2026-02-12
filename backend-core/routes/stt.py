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
<<<<<<< HEAD
<<<<<<< HEAD
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/0")
celery_app = Celery("ai_worker", broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)

=======
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery("ai_worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.result_backend = CELERY_RESULT_BACKEND
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery("ai_worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.result_backend = CELERY_RESULT_BACKEND
>>>>>>> 린_phase4

@router.post("/recognize")
async def recognize_audio(file: UploadFile = File(...)):
    """
<<<<<<< HEAD
<<<<<<< HEAD
    오디오 파일을 AI-Worker로 전송하여 STT 수행
    
    Args:
        file (UploadFile): 오디오 파일
        
    Returns:
        dict: STT 결과
=======
    오디오 파일을 AI-Worker로 전송하여 STT 수행 (Queue: cpu_queue)
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
    오디오 파일을 AI-Worker로 전송하여 STT 수행 (Queue: cpu_queue)
>>>>>>> 린_phase4
    """
    try:
        # 파일 읽기
        audio_content = await file.read()
        
<<<<<<< HEAD
<<<<<<< HEAD
        # Base64 인코딩 (Celery JSON Serialization 호환)
=======
=======
>>>>>>> 린_phase4
        if not audio_content:
            logger.error("Empty audio file received")
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Base64 인코딩
<<<<<<< HEAD
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
>>>>>>> 린_phase4
        audio_b64 = base64.b64encode(audio_content).decode('utf-8')
        
        # AI-Worker에 작업 요청 (Celery)
        logger.info(f"Sending STT task to AI-Worker (size: {len(audio_content)} bytes)")
        
<<<<<<< HEAD
<<<<<<< HEAD
=======
        # 명시적으로 cpu_queue 지정
>>>>>>> 린_phase4
        task = celery_app.send_task(
            "tasks.stt.recognize",
            args=[audio_b64],
            queue="cpu_queue"
        )
        
        # 결과 대기 (최대 300초: 모델 로딩 시간 고려)
        try:
            result = await asyncio.to_thread(task.get, timeout=300)
        except Exception as e:
            logger.error(f"Task execution failed or timed out: {e}")
            raise HTTPException(status_code=504, detail="Task Timed Out")

        if isinstance(result, dict) and result.get("status") == "error":
             error_msg = result.get("message", "Unknown error")
<<<<<<< HEAD
=======
        # 명시적으로 cpu_queue 지정
        task = celery_app.send_task(
            "tasks.stt.recognize",
            args=[audio_b64],
            queue="cpu_queue"
        )
        
        # 결과 대기 (최대 300초: 모델 로딩 시간 고려)
        try:
            result = await asyncio.to_thread(task.get, timeout=300)
        except Exception as e:
            logger.error(f"Task execution failed or timed out: {e}")
            raise HTTPException(status_code=504, detail="Task Timed Out")

        if isinstance(result, dict) and result.get("status") == "error":
             error_msg = result.get("message", "Unknown error")
             logger.error(f"Worker returned error: {error_msg}")
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
             logger.error(f"Worker returned error: {error_msg}")
>>>>>>> 린_phase4
             raise HTTPException(status_code=500, detail=f"Worker Error: {error_msg}")
             
        text = result.get("text", "") if isinstance(result, dict) else ""
        logger.info(f"STT Recognition Success: {len(text)} chars")
        return {"text": text}
        
<<<<<<< HEAD
<<<<<<< HEAD
=======
    except HTTPException:
        raise
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
    except HTTPException:
        raise
>>>>>>> 린_phase4
    except Exception as e:
        logger.error(f"STT Error: {e}", exc_info=True)
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

