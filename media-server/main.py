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
from vision_analyzer import VisionAnalyzer  # [NEW] MediaPipe Vision Analyzer
import io  # [NEW] 오디오 버퍼링용

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

# 4. Local Whisper 설정 (Removed: Delegated to AI-Worker)
# WHISPER_MODEL = None

class VideoAnalysisTrack(MediaStreamTrack):
    """비디오 프레임을 추출하여 ai-worker에 감정 분석을 요청하는 트랙"""
    kind = "video"

    def __init__(self, track, session_id):
        super().__init__()
        self.track = track
        self.session_id = session_id
        self.last_frame_time = 0

        self.last_frame_time = 0

        # [변경 내역: 2026-02-11]
        # 이전 코드 (Legacy):
        # self.face_cascade = cv2.CascadeClassifier(...) -> OpenCV Haar Cascade 사용 (구형, CPU 부하 높음)
        # self.eye_cascade = cv2.CascadeClassifier(...)
        #
        # 변경 코드 (New):
        # self.analyzer = VisionAnalyzer() -> MediaPipe 기반 최신 분석기 사용
        #
        # 변경 이유:
        # 1. 3D Face Landmark (478개 점) 추적으로 정밀도 향상
        # 2. 감정(Blendshapes), 시선, 자세 분석을 한 번의 추론으로 통합 (효율성)
        # 3. GPU/CPU 최적화된 MediaPipe 사용으로 실시간성 확보
        self.analyzer = VisionAnalyzer()
        logger.info(f"[{session_id}] VideoAnalysisTrack initialized with MediaPipe")


    async def process_vision(self, frame, timestamp_ms):
        """WebRTC 프레임 -> MediaPipe 분석 -> WebSocket 전송"""
        # [변경 내역: 2026-02-11]
        # 이전 함수명: process_eye_tracking
        # 이전 로직: OpenCV로 얼굴/눈 사각형만 찾아서 좌표 보냄. 감정 분석은 별도로 Celery 태스크로 보냄.
        #
        # 변경 로직:
        # 1. process_vision으로 통합.
        # 2. MediaPipe가 얼굴+눈+감정+자세를 한 번에 분석.
        # 3. WebSocket으로 'vision_analysis'라는 통합된 데이터 전송.
        try:
            # OpenCV 포맷 변환
            img = frame.to_ndarray(format="bgr24")
            
            # [NEW] MediaPipe 분석 실행
            result = self.analyzer.process_frame(img, timestamp_ms)
            
            if result:
                # 1. 터미널 로그 (디버깅용, 2초마다)
                current_time = time.time()
                if current_time - getattr(self, 'last_log_time', 0) > 2.0:
                    self.last_log_time = current_time
                    logger.info(f"[{self.session_id}] Vision: {result['emotion']} / {result['gaze']} (Smile: {result['scores']['smile']})")

                # 2. WebSocket 전송 (프론트엔드 시각화용)
                ws = active_websockets.get(self.session_id)
                if ws:
                    await send_to_websocket(ws, {
                        "type": "vision_analysis", # 통합된 비전 데이터 타입
                        "data": result,
                        "timestamp": current_time
                    })
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")

    async def recv(self):
        frame = await self.track.recv()
        current_time = time.time()

        # 1. 비전 분석 (실시간성 중요 - 0.1초마다 수행)
        if current_time - getattr(self, 'last_tracking_time', 0) > 0.1:
            self.last_tracking_time = current_time
            # 비동기로 실행하여 메인 스트림 지연 방지
            # timestamp용으로 time.time() * 1000 사용
            asyncio.create_task(self.process_vision(frame, int(current_time * 1000)))

        # 2. (구버전) 감정 분석 태스크 호출 제거
        # MediaPipe가 감정까지 다 하므로 더 이상 필요 없음.
        # if current_time - self.last_frame_time > 2.0: ...

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
                
                # (Optional) 결과를 비동기로 기다리는 로직을 추가하려면 asyncio.to_thread 등 사용
                # 하지만 실시간 스트리밍에서 Celery RTT는 지연이 발생할 수 있음.
                
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
# [추가 내역: 2026-02-11]
# STT 중계 함수 (Remote STT)
# WebRTC 오디오 스트림 -> WAV 파일 변환 -> AI Worker로 전송
async def start_remote_stt(track, session_id):
    logger.info(f"[{session_id}] 🎙️ 원격 STT 시작 (Remote STT Started)")
    
    # 3초 단위로 오디오를 모아서 전송 (VAD 없이 시간 기반 분할)
    CHUNK_DURATION_MS = 3000 
    accumulated_frames = []
    accumulated_time = 0
    
    try:
        while True:
            # 1. 오디오 프레임 수신
            frame = await track.recv()
            accumulated_frames.append(frame)
            
            # 프레임 시간 누적 (packet.duration 사용하거나 개수로 추정)
            # 보통 Opus 프레임은 20ms or 60ms
            # 여기서는 프레임 개수로 대략적인 시간 계산 (50개 = 약 1초 가정)
            # 정확성을 위해 av.AudioFrame.time 사용 가능하지만 단순화
            if len(accumulated_frames) >= 150: # 약 3초 (20ms * 150 = 3000ms)
                
                # 2. WAV 변환 (In-Memory)
                # av 라이브러리의 Output Container 사용
                output_buffer = io.BytesIO()
                output_container = av.open(output_buffer, mode='w', format='wav')
                output_stream = output_container.add_stream('pcm_s16le', rate=16000, layout='mono')
                
                for f in accumulated_frames:
                    # 리샘플링 및 패킷 작성
                    for packet in output_stream.encode(f):
                        output_container.mux(packet)
                        
                # 3. 마무리 (Flush)
                for packet in output_stream.encode(None):
                    output_container.mux(packet)
                output_container.close()
                
                # 4. Base64 인코딩
                wav_bytes = output_buffer.getvalue()
                audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
                
                # 5. Celery Task 배달 (AI Worker에게)
                # 결과값은 비동기로 처리되므로, 여기서는 '보냈다'는 사실만 중요
                celery_app.send_task(
                    "tasks.stt.recognize",
                    args=[audio_b64],
                    queue="gpu_queue" # GPU 워커 전용 큐 사용
                )
                
                logger.info(f"[{session_id}] 📤 오디오 청크 전송 완료 ({len(wav_bytes)} bytes)")
                
                # 버퍼 초기화
                accumulated_frames = []

    except Exception as e:
        logger.info(f"[{session_id}] STT 스트림 종료: {e}")
    finally:
        logger.info(f"[{session_id}] STT 리소스 정리")


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
    @pc.on("track")
    def on_track(track):
        logger.info(f"[{session_id}] Received track: {track.kind}")

        if track.kind == "audio":
            # [변경 내역: 2026-02-11]
            # 1. 이전 코드의 `start_stt_with_local_whisper` 함수는 정의되지 않아 서버 크래시를 유발했습니다.
            # 2. 미디어 서버에서 모델을 직접 돌리면 비디오 중계가 렉걸릴 수 있으므로,
            #    무거운 STT 작업은 전용 GPU 워커(AI-Worker)에게 위임(Delegate)합니다.
            asyncio.ensure_future(start_remote_stt(track, session_id))
            logger.info(f"[{session_id}] Audio track processing started (Remote STT via AI-Worker)")
            
        elif track.kind == "video":
            # 비디오 트랙: 감정 분석 처리
            pc.addTrack(VideoAnalysisTrack(relay.subscribe(track), session_id))
            logger.info(f"[{session_id}] Video analysis track added")

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

# [복구: 2026-02-12]
# EnvTestPage.jsx 테스트를 위한 필수 엔드포인트
from fastapi import UploadFile, File, HTTPException

@app.post("/stt/recognize")
async def stt_recognize(file: UploadFile = File(...)):
    """
    STT 테스트용 엔드포인트 (EnvTestPage.jsx에서 호출)
    """
    try:
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        task = celery_app.send_task(
            "tasks.stt.recognize",
            args=[audio_b64],
            queue="gpu_queue"
        )
        # 테스트용이므로 결과 대기
        result = task.get(timeout=30)
        return result
    except Exception as e:
        logger.error(f"STT Test Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
