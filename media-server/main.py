import asyncio
import json
import logging
import os
import base64
import time
import cv2
from typing import Dict, Set
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay
from celery import Celery

# 1. 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Media-Server")

app = FastAPI()

# CORS 설정 (프론트엔드 연결 허용)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

relay = MediaRelay()

# 2. Celery 설정 (ai-worker로 감정 분석 요청 전달용)
celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# 3. WebSocket 연결 관리 (세션별 WebSocket 저장)
active_websockets: Dict[str, WebSocket] = {}

# 4. Deepgram 설정 (STT가 활성화된 경우에만)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
USE_DEEPGRAM = bool(DEEPGRAM_API_KEY)

if USE_DEEPGRAM:
    try:
        from deepgram import DeepgramClient
        from deepgram.core.events import EventType
        logger.info("✅ Deepgram SDK v5+ loaded successfully")
    except ImportError as e:
        logger.error(f"❌ deepgram-sdk import failed: {e}")
        USE_DEEPGRAM = False
    except Exception as e:
        logger.warning(f"⚠️ Error loading Deepgram SDK: {e}. STT will be disabled.")
        USE_DEEPGRAM = False
else:
    logger.warning("⚠️ DEEPGRAM_API_KEY not set. STT will be disabled.")

import threading

class VideoAnalysisTrack(MediaStreamTrack):
    """비디오 프레임을 추출하여 ai-worker에 감정 분석을 요청하는 트랙"""
    kind = "video"

    def __init__(self, track, session_id):
        super().__init__()
        self.track = track
        self.session_id = session_id
        self.last_frame_time = 0

    async def recv(self):
        frame = await self.track.recv()
        current_time = time.time()

        # 2초마다 한 번씩 프레임 추출 (CPU 부하 방지 및 4650G 최적화)
        if current_time - self.last_frame_time > 2.0:
            self.last_frame_time = current_time
            
            # 프레임을 이미지로 변환
            img = frame.to_ndarray(format="bgr24")
            _, buffer = cv2.imencode('.jpg', img)
            base64_img = base64.b64encode(buffer).decode('utf-8')

            # ai-worker에 비동기 감정 분석 태스크 전달 (JSON 포맷 데이터)
            celery_app.send_task(
                "tasks.vision.analyze_emotion",
                args=[self.session_id, base64_img]
            )
            logger.info(f"[{self.session_id}] 감정 분석 프레임 전송 완료")

        return frame

async def start_stt_with_deepgram(audio_track: MediaStreamTrack, session_id: str):
    """Deepgram 실시간 STT 실행 (SDK v5 Sync Pattern with Threading)"""
    if not USE_DEEPGRAM:
        logger.warning(f"[{session_id}] Deepgram 비활성화 상태. STT 건너뜀.")
        return
    
    try:
        # Deepgram 클라이언트 초기화 (v5 방식)
        deepgram = DeepgramClient()
        
        # 연결 옵션
        options = {
            "model": "nova-2",
            "language": "ko",
            "smart_format": True,
            "encoding": "linear16",
            "channels": 1,
            "sample_rate": 16000,
        }

        # Thread-safe WebSocket sending helper
        loop = asyncio.get_running_loop()
        
        # Deepgram v5 Sync Connect Pattern
        # Note: using with statement as per docs / user snippet
        with deepgram.listen.v1.connect(**options) as connection:
            logger.info(f"[{session_id}] Deepgram V5 Connection Established")

            def on_message(message, **kwargs):
                """Callback for receiving transcripts"""
                try:
                    # message는 ListenV1SocketClientResponse 타입
                    # user snippet logic:
                    if hasattr(message, 'channel') and hasattr(message.channel, 'alternatives'):
                        sentence = message.channel.alternatives[0].transcript
                        if len(sentence) == 0:
                            return
                        
                        logger.info(f"[{session_id}] STT: {sentence}")
                        
                        stt_data = {
                            "session_id": session_id,
                            "text": sentence,
                            "type": "stt_result",
                            "timestamp": time.time()
                        }
                        
                        # Bridge to Asyncio Loop for WebSocket
                        if session_id in active_websockets:
                            ws = active_websockets[session_id]
                            asyncio.run_coroutine_threadsafe(send_to_websocket(ws, stt_data), loop)

                except Exception as e:
                    logger.error(f"[{session_id}] on_message Error: {e}")

            def on_error(error, **kwargs):
                logger.error(f"[{session_id}] Deepgram Error: {error}")

            # Register Events
            connection.on(EventType.MESSAGE, on_message)
            connection.on(EventType.ERROR, on_error)
            # connection.on(EventType.OPEN, lambda _: logger.info(f"[{session_id}] Deepgram Connected"))
            
            # Start listening in a separate thread (Blocking call)
            def listening_thread_func():
                try:
                    connection.start_listening()
                except Exception as e:
                    logger.error(f"[{session_id}] Listening Thread Error: {e}")

            listen_thread = threading.Thread(target=listening_thread_func, daemon=True)
            listen_thread.start()

            try:
                # Main Audio Send Loop (Async)
                logger.info(f"[{session_id}] Starting Audio Stream to Deepgram...")
                frame_count = 0
                while True:
                    try:
                        frame = await audio_track.recv()
                        frame_count += 1
                        
                        audio_data = frame.to_ndarray().tobytes()
                        
                        # Send media (Sync call inside Async loop - assumes low overhead)
                        connection.send_media(audio_data)
                        
                        if frame_count % 100 == 0:
                            logger.debug(f"[{session_id}] Sent {frame_count} frames")
                            
                    except Exception as e:
                        logger.warning(f"[{session_id}] Audio Stream Ended/Error: {e}")
                        break
            finally:
                # Loop ends when track closes
                logger.info(f"[{session_id}] Audio track closed. Finishing Deepgram session...")
                # Context manager exit will automatically call finish(), but explicit call ensures thread unblocks
                connection.finish()
            
            # Wait for listening thread to exit
            listen_thread.join(timeout=2.0)
            if listen_thread.is_alive():
                logger.warning(f"[{session_id}] Deepgram listening thread did not exit cleanly")
            else:
                logger.info(f"[{session_id}] Deepgram listening thread finished")

    except Exception as e:
        logger.error(f"[{session_id}] Deepgram Init Failed: {e}")


async def send_to_websocket(ws: WebSocket, data: dict):
    """WebSocket으로 데이터 전송 (에러 처리 포함)"""
    try:
        await ws.send_json(data)
    except Exception as e:
        logger.error(f"WebSocket 전송 실패: {e}")

# ============== WebSocket 엔드포인트 ==============
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """프론트엔드와 실시간 STT 결과 공유를 위한 WebSocket 연결"""
    await websocket.accept()
    active_websockets[session_id] = websocket
    logger.info(f"[{session_id}] ✅ WebSocket 연결 성공")
    
    try:
        # 연결 유지 및 클라이언트로부터 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            # 필요 시 클라이언트로부터 받은 메시지 처리
            logger.debug(f"[{session_id}] Received from client: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"[{session_id}] ❌ WebSocket 연결 종료")
    except Exception as e:
        logger.error(f"[{session_id}] WebSocket 에러: {e}")
    finally:
        # 연결 종료 시 세션 제거
        if session_id in active_websockets:
            del active_websockets[session_id]
            logger.info(f"[{session_id}] WebSocket 세션 정리 완료")

# ============== WebRTC 엔드포인트 ==============
@app.post("/offer")
async def offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    session_id = params.get("session_id", "unknown")

    pc = RTCPeerConnection()
    logger.info(f"[{session_id}] WebRTC 연결 시도")

    @pc.on("track")
    def on_track(track):
        logger.info(f"[{session_id}] Received track: {track.kind}")
        if track.kind == "audio":
            asyncio.ensure_future(start_stt_with_deepgram(track, session_id))
            logger.info(f"[{session_id}] Audio track processing started (STT enabled)")
        elif track.kind == "video":
            pc.addTrack(VideoAnalysisTrack(relay.subscribe(track), session_id))
            logger.info(f"[{session_id}] Video track processing started (Emotion analysis enabled)")
        else:
            logger.warning(f"[{session_id}] Unknown track type: {track.kind}")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }

@app.get("/")
async def root():
    return {
        "service": "AI Interview Media Server",
        "status": "running",
        "websocket_endpoint": "/ws/{session_id}",
        "webrtc_endpoint": "/offer",
        "deepgram_enabled": USE_DEEPGRAM
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")