from fastapi import APIRouter, UploadFile, File, HTTPException, status, WebSocket
from huggingface_hub import InferenceClient
import os
import logging
import asyncio

logger = logging.getLogger("STT-Service")

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])

# Hugging Face 설정
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "openai/whisper-large-v3-turbo"


@router.post("/recognize")
async def recognize_audio(file: UploadFile = File(...)):
    """
    오디오 파일을 업로드 받아 Hugging Face API를 통해 텍스트로 변환
    Note: Hugging Face Inference API 사용 (Serverless)
    """
    if not HF_TOKEN:
        logger.error("HF_TOKEN environment variable is not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: HF_TOKEN missed"
        )
    
    try:
        # 파일 읽기
        audio_content = await file.read()
        
        # Hugging Face Inference Client 초기화
        client = InferenceClient(token=HF_TOKEN)
        
        # ASR 요청 (Automatic Speech Recognition)
        # Whisper 모델은 오디오 파일(bytes)을 직접 받아 처리 가능
        response = client.automatic_speech_recognition(
            audio_content, 
            model=MODEL_ID
        )
        
        # 응답 처리 (Hugging Face API는 {"text": "..."} 형태 반환)
        text = response.text if hasattr(response, 'text') else str(response)
        
        logger.info(f"STT Recognition Success: {len(text)} chars")
        return {"text": text}
        
    except Exception as e:
        logger.error(f"STT Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STT processing failed: {str(e)}"
        )


@router.websocket("/ws/{interview_id}")
async def stt_websocket(websocket: WebSocket, interview_id: int):
    """
    [Deprecated] WebSocket STT Endpoint
    
    Deepgram 스트리밍을 사용하던 기존 엔드포인트입니다.
    Hugging Face Whisper 모델로 전환되면서, 
    실시간 스트리밍 대신 프론트엔드 VAD + REST API (/recognize) 방식을 사용해야 합니다.
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "error",
        "message": "WebSocket STT is deprecated. Please use POST /api/stt/recognize with audio file."
    })
    await websocket.close()

