import asyncio
import json
import logging
import os
import base64
import time
import cv2
from typing import Dict, Set
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay
from celery import Celery
import av

# 1. 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Media-Server")

app = FastAPI()

# CORS 설정
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite 개발 서버
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

relay = MediaRelay()

# 2. Celery 설정
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("ai_worker", broker=redis_url, backend=redis_url)

# 3. WebSocket 연결 관리 (세션별 WebSocket 저장)
active_websockets: Dict[str, WebSocket] = {}

class VideoAnalysisTrack(MediaStreamTrack):
    """비디오 프레임을 추출하여 ai-worker에 감정 분석을 요청하는 트랙"""
    kind = "video"

    def __init__(self, track, session_id):
        super().__init__()
        self.track = track
        self.session_id = session_id
        self.last_frame_time = 0

        # Haar Cascade Load
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')


    async def process_eye_tracking(self, frame):
        """WebRTC 프레임에서 눈/얼굴 추적 후 WebSocket 전송"""
        try:
            # OpenCV 형식으로 변환
            img = frame.to_ndarray(format="bgr24")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            tracking_data = []
            
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                
                eyes_coords = []
                for (ex, ey, ew, eh) in eyes:
                    eyes_coords.append({
                        "x": int(x + ex),
                        "y": int(y + ey),
                        "w": int(ew),
                        "h": int(eh)
                    })
                
                tracking_data.append({
                    "face": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "eyes": eyes_coords
                })

            # Status determination
            status = "not_detected"
            if len(tracking_data) > 0:
                face = tracking_data[0] # Assuming first face
                num_eyes = len(face["eyes"])
                
                if num_eyes >= 2:
                    status = "focused"
                elif num_eyes == 1:
                    status = "partially_detected"
                else:
                    status = "eyes_not_visible"
            
            # Log status (throttled)
            current_time = time.time()
            if current_time - getattr(self, 'last_log_time', 0) > 2.0: # Log every 2 seconds
                self.last_log_time = current_time
                logger.info(f"[{self.session_id}] Eye Tracking Status: {status} (Faces: {len(faces)})")

            # WebSocket으로 전송
            ws = active_websockets.get(self.session_id)
            if ws:
                await send_to_websocket(ws, {
                    "type": "eye_tracking",
                    "data": tracking_data,
                    "status": status  # Send status to frontend as well
                })

        except Exception as e:
            logger.error(f"Eye tracking frame failed: {e}")

    async def recv(self):
        frame = await self.track.recv()
        current_time = time.time()

        # 1. 눈 추적 (실시간성 중요 - 0.1초마다 수행)
        # 모든 프레임을 하면 부하가 클 수 있으므로 간격 조절
        if current_time - getattr(self, 'last_tracking_time', 0) > 0.1:
            self.last_tracking_time = current_time
            # 비동기로 실행하여 메인 스트림 지연 방지
            asyncio.create_task(self.process_eye_tracking(frame))

        # 2. 감정 분석 (무거운 작업 - 2초마다 수행)
        if current_time - self.last_frame_time > 2.0:
            self.last_frame_time = current_time
            
            # 프레임을 이미지로 변환
            img = frame.to_ndarray(format="bgr24")
            _, buffer = cv2.imencode('.jpg', img)
            base64_img = base64.b64encode(buffer).decode('utf-8')

            # ai-worker에 비동기 감정 분석 태스크 전달
            celery_app.send_task(
                "tasks.vision.analyze_emotion",
                args=[self.session_id, base64_img]
            )
            # 눈 추적 Task도 호출하여 데이터 저장 (선택적)
            # celery_app.send_task("tasks.vision.track_eyes", args=[self.session_id, base64_img])

        return frame

async def start_remote_stt(track, session_id):
    """
    AI-Worker에게 오디오 청크를 전송하여 STT 처리 (Remote STT)
    """
    logger.info(f"[{session_id}] Remote STT Task Loop Started")
    
    audio_buffer = []
    # 2초 분량 모아서 전송 (빈번한 Task 생성 방지)
    # 16kHz, 16bit(2bytes), Mono -> 2초 = 16000 * 2 * 2 = 64000 bytes
    BUFFER_SIZE = 64000 
    
    try:
        while True:
            frame = await track.recv()
            
            # 1. 리샘플링 (WebRTC 48k -> Whisper 16k)
            resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
            resampled_frames = resampler.resample(frame)
            
            for f in resampled_frames:
                # av.AudioFrame.to_ndarray() -> numpy array
                # tobytes()로 raw bytes 추출
                data = f.to_ndarray().tobytes()
                audio_buffer.append(data)
                
            # 2. 버퍼 크기 확인
            current_size = sum(len(b) for b in audio_buffer)
            
            if current_size >= BUFFER_SIZE:
                # 청크 병합
                full_audio = b"".join(audio_buffer)
                audio_buffer = [] # 초기화
                
                # Base64 인코딩
                b64_audio = base64.b64encode(full_audio).decode('utf-8')
                
                # 3. AI-Worker로 Task 전송
                # Celery는 비동기이므로 여기서 결과를 기다리지 않고 Task만 큐에 넣음
                # 필요 시 결과 처리를 위한 별도 메커니즘 필요 (예: Task가 결과 DB에 쓰고 Polling 등)
                task = celery_app.send_task(
                    "tasks.stt.recognize",
                    args=[b64_audio]
                )
                logger.debug(f"[{session_id}] Sent STT chunk to AI-Worker. Task ID: {task.id}")
                
                # [추가] STT 결과 대기 및 WebSocket 전송
                async def wait_for_stt_result(task_id, sid):
                    try:
                        # Celery AsyncResult로 결과 추적
                        from celery.result import AsyncResult
                        res = AsyncResult(task_id, app=celery_app)
                        
                        # 최대 5초 대기
                        start_wait = time.time()
                        while not res.ready():
                            await asyncio.sleep(0.1)
                            if time.time() - start_wait > 5.0:
                                return
                        
                        text_result = res.result
                        if text_result and text_result.strip():
                            ws = active_websockets.get(sid)
                            if ws:
                                await send_to_websocket(ws, {
                                    "type": "stt_result",
                                    "text": text_result
                                })
                                logger.info(f"[{sid}] 🎤 STT Result Sent: {text_result[:30]}...")
                    except Exception as ex:
                        logger.error(f"[{sid}] Error waiting for STT result: {ex}")

                # 비동기적으로 결과 대기 루프 실행 (메인 루프 차단 방지)
                asyncio.create_task(wait_for_stt_result(task.id, session_id))
                
    except Exception as e:
        logger.error(f"[{session_id}] Remote STT Fail: {e}")
    finally:
        logger.info(f"[{session_id}] Remote STT Stopped")

async def send_to_websocket(ws: WebSocket, data: dict):
    """WebSocket으로 데이터 전송"""
    try:
        await ws.send_json(data)
    except Exception as e:
        logger.error(f"WebSocket 전송 실패: {e}")

# ============== WebSocket 엔드포인트 ==============
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_websockets[session_id] = websocket
    logger.info(f"[{session_id}] ✅ WebSocket 연결 성공")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 대기 (현재는 특별한 처리 없음)
            await websocket.receive_text()
            
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

    # STUN 서버 설정은 유지 (비디오 연결 안정성을 위해)
    pc = RTCPeerConnection(
        configuration=RTCConfiguration(
            iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
        )
    )
    logger.info(f"[{session_id}] WebRTC 연결 시도")

    @pc.on("track")
    def on_track(track):
        logger.info(f"[{session_id}] Received track: {track.kind}")
        if track.kind == "video":
            # 비디오 트랙: 감정 분석 처리
            pc.addTrack(VideoAnalysisTrack(relay.subscribe(track), session_id))
            logger.info(f"[{session_id}] Video analysis track added")
        elif track.kind == "audio":
            # [변경] AI Worker로 위임 (Remote STT)
            asyncio.ensure_future(start_remote_stt(track, session_id))
            logger.info(f"[{session_id}] Audio track processing started (Remote STT)")
        else:
            logger.warning(f"[{session_id}] Unknown track type: {track.kind}")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }

async def consume_audio(track):
    """오디오 트랙을 소비하여 버퍼가 차지 않도록 함"""
    try:
        while True:
            await track.recv()
    except Exception:
        # 트랙이 종료되면 예외 발생 (정상적인 종료)
        pass

@app.get("/")
async def root():
    return {
        "service": "AI Interview Media Server",
        "status": "running",
        "mode": "Video Analysis + Remote STT (via AI-Worker)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")