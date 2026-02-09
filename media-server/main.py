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
import numpy as np
from faster_whisper import WhisperModel

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

# 4.1 Local Whisper 설정
WHISPER_MODEL = None
LOCAL_MODEL_SIZE = "large-v3-turbo" # or small, medium, etc.

def load_local_whisper():
    global WHISPER_MODEL
    try:
        if WHISPER_MODEL is None:
            logger.info(f"⏳ Loading Local Whisper Model ({LOCAL_MODEL_SIZE})...")
            # Run on GPU with FP16
            WHISPER_MODEL = WhisperModel(LOCAL_MODEL_SIZE, device="cuda", compute_type="float16")
            logger.info("✅ Local Whisper Model Loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load Local Whisper: {e}")

import threading

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
            # VAD 및 발화 감지 옵션 추가
            "interim_results": True,      # 중간 결과 수신 (빠른 피드백)
            "vad_events": True,           # 발화 시작(SpeechStarted) 감지 활성화
            "utterance_end_ms": "3000",   # 1초 침묵 시 발화 종료로 간주
            # "endpointing": 300            # (선택) 더 빠른 문장 종결 처리
        }

        # Deepgram 요구사항에 맞게 오디오 변환 (16kHz, Mono, s16le)
        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)

        # Thread-safe WebSocket sending helper
        loop = asyncio.get_running_loop()

        # [중요] Deepgram 연결 타임아웃 방지: 첫 오디오 프레임이 도착할 때까지 대기
        try:
            logger.info(f"[{session_id}] Waiting for first audio frame...")
            first_frame = await audio_track.recv()
            logger.info(f"[{session_id}] First audio frame received. Connecting to Deepgram...")
        except Exception as e:
            logger.warning(f"[{session_id}] Failed to receive first frame: {e}")
            return
        
        # Deepgram v5 Sync Connect Pattern
        with deepgram.listen.v1.connect(**options) as connection:
            logger.info(f"[{session_id}] Deepgram V5 Connection Established")

            def on_message(message, **kwargs):
                """Callback for receiving transcripts & events"""
                try:
                    # 1. 메시지 타입 확인 (SpeechStarted 등)
                    msg_type = getattr(message, "type", "Result")
                    
                    if msg_type == "SpeechStarted":
                        logger.info(f"[{session_id}] 🗣️ Speech Started detected")
                        # 프론트엔드에 발화 시작 알림 (말하기 시작했음을 UI에 표시 가능)
                        event_data = {
                            "session_id": session_id,
                            "type": "speech_started",
                            "timestamp": time.time()
                        }
                        if session_id in active_websockets:
                            ws = active_websockets[session_id]
                            asyncio.run_coroutine_threadsafe(send_to_websocket(ws, event_data), loop)
                        return

                    # 2. 일반 Transcript 처리
                    if hasattr(message, 'channel') and hasattr(message.channel, 'alternatives'):
                        alt = message.channel.alternatives[0]
                        sentence = alt.transcript
                        
                        if len(sentence) == 0:
                            return
                        
                        # 최종 결과(final)만 로그 또는 처리할 수도 있고, interim도 보낼 수 있음
                        is_final = message.is_final if hasattr(message, 'is_final') else False
                        
                        # 로그에는 Final만, 프론트엔드에는 둘 다 전송하여 실시간성을 높임
                        if is_final:
                            logger.info(f"[{session_id}] STT (Final): {sentence}")
                        
                        stt_data = {
                            "session_id": session_id,
                            "text": sentence,
                            "type": "stt_result",
                            "is_final": is_final,
                            "timestamp": time.time()
                        }
                        
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
                # 1. 첫 번째 프레임 처리 (이미 받았으므로)
                try:
                    transformed = resampler.resample(first_frame)
                    for tf in transformed:
                        connection.send_media(tf.to_ndarray().tobytes())
                except Exception as e:
                    logger.error(f"[{session_id}] Error sending first frame: {e}")

                # 2. 이후 프레임 루프
                logger.info(f"[{session_id}] Streaming audio to Deepgram...")
                frame_count = 1
                while True:
                    try:
                        frame = await audio_track.recv()
                        frame_count += 1
                        
                        # WebRTC AudioFrame(보통 48kHz, Stereo) -> Deepgram(16kHz, Mono) 변환
                        # 변환하지 않으면 Deepgram이 데이터를 인식하지 못해 Timeout(1011) 발생 가능
                        transformed_frames = resampler.resample(frame)
                        
                        for tf in transformed_frames:
                            audio_data = tf.to_ndarray().tobytes()
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

async def start_stt_with_local_whisper(audio_track: MediaStreamTrack, session_id: str):
    """Local Faster-Whisper 실시간 STT 실행 (Buffering approach)"""
    
    logger.info(f"[{session_id}] ⭐ start_stt_with_local_whisper CALLED - Function entered successfully")
    
    # 모델 로딩 (최초 1회)
    if WHISPER_MODEL is None:
        load_local_whisper()
    
    if WHISPER_MODEL is None:
        logger.error(f"[{session_id}] Local Whisper Model not available.")
        return

    try:
        logger.info(f"[{session_id}] Starting Local Whisper STT Stream...")
        loop = asyncio.get_running_loop()
        
        # Whisper는 16kHz, Mono, Float32 입력을 기대함
        resampler = av.AudioResampler(format='flt', layout='mono', rate=16000)
        
        buffer = [] # Float32 samples accumulation
        BUFFER_DURATION_SEC = 1.0 # [수정] 2초 → 1초로 단축 (짧은 답변 인식 개선)
        SAMPLE_RATE = 16000
        CHUNK_SIZE = int(SAMPLE_RATE * BUFFER_DURATION_SEC)
        
        # 이전 텍스트 중복 방지용
        last_text = ""

        frame_count = 0
        while True:
            try:
                frame = await audio_track.recv()
                frame_count += 1
                
                # Resample & Convert to Numpy
                frame_resampled = resampler.resample(frame)
                for f in frame_resampled:
                    # to_ndarray returns (1, samples) for stereo or mono depending on layout
                    # format='flt' -> float32
                    chunk = f.to_ndarray()[0] 
                    buffer.extend(chunk)
                
                # 프레임 수신 로그 (10프레임마다)
                if frame_count % 10 == 0:
                    logger.info(f"[{session_id}] 📊 Received {frame_count} frames, buffer size: {len(buffer)}")
                
                # 버퍼가 일정 크기 이상 쌓이면 추론 실행
                if len(buffer) >= CHUNK_SIZE:
                    logger.info(f"[{session_id}] 🎤 Buffer full ({len(buffer)} samples), starting transcription...")
                    audio_data = np.array(buffer, dtype=np.float32)
                    buffer = [] # 버퍼 초기화 (또는 오버랩 구현 가능)

                    # VAD Filter를 켜서 무음 구간 제외하고 인식
                    segments, info = WHISPER_MODEL.transcribe(audio_data, language="ko", vad_filter=True)
                    
                    text_segments = [s.text for s in segments]
                    current_text = " ".join(text_segments).strip()
                    
                    if not current_text:
                        logger.info(f"[{session_id}] 🔇 No active speech detected (Silence/VAD)")
                    elif current_text == last_text:
                        logger.info(f"[{session_id}] 🔁 Duplicate text (ignored): {current_text}")
                    else:
                        logger.info(f"[{session_id}] Local STT: {current_text}")
                        last_text = current_text
                        
                        stt_data = {
                            "session_id": session_id,
                            "text": current_text,
                            "type": "stt_result",
                            "is_final": True, # 로컬 배치는 항상 Final로 취급
                            "timestamp": time.time()
                        }
                        
                        if session_id in active_websockets:
                            ws = active_websockets[session_id]
                            asyncio.run_coroutine_threadsafe(send_to_websocket(ws, stt_data), loop)

            except Exception as e:
                logger.error(f"[{session_id}] Local Whisper Stream Error/End: {e}", exc_info=True)
                break
        
        # [중요] 스트림 종료 시 남은 버퍼 처리 (짧은 답변 보존)
        if len(buffer) > 0:
            logger.info(f"[{session_id}] 🔚 Processing remaining {len(buffer)} samples before stream end...")
            try:
                audio_data = np.array(buffer, dtype=np.float32)
                segments, info = WHISPER_MODEL.transcribe(audio_data, language="ko", vad_filter=True)
                text_segments = [s.text for s in segments]
                final_text = " ".join(text_segments).strip()
                
                if final_text and final_text != last_text:
                    logger.info(f"[{session_id}] Local STT (final): {final_text}")
                    stt_data = {
                        "session_id": session_id,
                        "text": final_text,
                        "type": "stt_result",
                        "is_final": True,
                        "timestamp": time.time()
                    }
                    if session_id in active_websockets:
                        ws = active_websockets[session_id]
                        asyncio.run_coroutine_threadsafe(send_to_websocket(ws, stt_data), loop)
            except Exception as e:
                logger.error(f"[{session_id}] Error processing final buffer: {e}")
                
        logger.info(f"[{session_id}] Local Whisper Stream Finished")

    except Exception as e:
        logger.error(f"[{session_id}] Local STT Init Error: {e}")



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

        if track.kind == "audio":
            # [변경] Deepgram 대신 Local Whisper 사용
            # asyncio.ensure_future(start_stt_with_deepgram(track, session_id))
            asyncio.ensure_future(start_stt_with_local_whisper(track, session_id))
            logger.info(f"[{session_id}] Audio track processing started (Local Whisper enabled)")
        elif track.kind == "video":
            pc.addTrack(VideoAnalysisTrack(relay.subscribe(track), session_id))
            logger.info(f"[{session_id}] Video analysis track added")
        elif track.kind == "audio":
            # 오디오 트랙: 서버에서는 처리하지 않음 (STT는 프론트엔드에서 수행)
            # 다만 WebRTC 연결 유지를 위해 트랙을 소비해주는 것이 좋음 (Blackhole)
            @track.on("ended")
            async def on_ended():
                logger.info(f"[{session_id}] Audio track ended")
            
            asyncio.ensure_future(consume_audio(track))
            logger.info(f"[{session_id}] Audio track ignored (Client-side STT used)")
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
        "mode": "Video Analysis Only (STT migrated to frontend)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
