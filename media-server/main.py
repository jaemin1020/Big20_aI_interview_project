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

# 3. 연결 관리 (세션별 WebSocket 및 PeerConnection 저장)
active_websockets: Dict[str, WebSocket] = {}
active_pcs: Dict[str, RTCPeerConnection] = {} # [추가] 세션별 PeerConnection 저장

class VideoAnalysisTrack(MediaStreamTrack):
    """비디오 프레임을 추출하여 ai-worker에 감정 분석을 요청하는 트랙"""
    kind = "video"

    def __init__(self, track, session_id):
        super().__init__()
        self.track = track
        self.session_id = session_id
        
        # [데이터 누적용] POC 세션 데이터 구조 이식
        self.analyzer = VisionAnalyzer()
        self.session_started_at = time.time()
        self.total_frames = 0
        
        # 질문별 데이터 (전체 합산을 위해 리스트로 관리)
        self.questions_history = [] 
        self.current_q_index = 0
        self.current_q_data = self._get_empty_q_data()
        
        # 실시간 로그 쿨타임
        self.last_log_time = 0
        self.last_tracking_time = 0
        
        logger.info(f"[{session_id}] VideoAnalysisTrack initialized with MediaPipe (CV-V2-TASK Logic)")

    def _get_empty_q_data(self):
        """새 질문을 위한 빈 데이터 구조 생성"""
        return {
            "smile_scores": [],
            "anxiety_scores": [],
            "gaze_center_frames": 0,
            "posture_stable_frames": 0,
            "total_frames": 0,
            "start_time": time.time()
        }

    def switch_question(self, new_index):
        """질문이 바뀔 때 호출 (from WebSocket)"""
        if self.current_q_data["total_frames"] > 0:
            # 이전 질문 결과 요약 로그 출력
            self._log_question_summary()
            self.questions_history.append(self.current_q_data)
        
        self.current_q_index = new_index
        self.current_q_data = self._get_empty_q_data()
        logger.info(f"[{self.session_id}] ➡️ Switched to Question {new_index}")

    def _log_question_summary(self):
        """질문별 중간 결과 로그 출력"""
        q = self.current_q_data
        total = q["total_frames"]
        if total == 0: return
        
        avg_smile = (sum(q["smile_scores"]) / total) * 100
        avg_anxiety = (sum(q["anxiety_scores"]) / total) * 100
        gaze_ratio = (q["gaze_center_frames"] / total) * 100
        posture_ratio = (q["posture_stable_frames"] / total) * 100
        
        logger.info(f"\n[{self.session_id}] 📝 Question {self.current_q_index} 중간 결과:")
        logger.info(f"   - 미소(자신감): {avg_smile:.1f}% | 긴장도: {avg_anxiety:.1f}%")
        logger.info(f"   - 시선 집중: {gaze_ratio:.1f}% | 자세 안정: {posture_ratio:.1f}%")

    def generate_final_report(self):
        """면접 종료 시 전체 합산 리포트 로그 출력 (POC 형식)"""
        if self.current_q_data["total_frames"] > 0:
            self.questions_history.append(self.current_q_data)
            
        if not self.questions_history:
            return

        total_frames = sum(q["total_frames"] for q in self.questions_history)
        if total_frames == 0: return

        all_smiles = []
        all_anxiety = []
        total_gaze_center = 0
        total_posture_stable = 0
        
        for q in self.questions_history:
            all_smiles.extend(q["smile_scores"])
            all_anxiety.extend(q["anxiety_scores"])
            total_gaze_center += q["gaze_center_frames"]
            total_posture_stable += q["posture_stable_frames"]

        avg_smile = (sum(all_smiles) / total_frames) * 100
        avg_anxiety = (sum(all_anxiety) / total_frames) * 100
        gaze_ratio = (total_gaze_center / total_frames) * 100
        posture_ratio = (total_posture_stable / total_frames) * 100
        
        score_conf = avg_smile * 0.3
        score_focus = gaze_ratio * 0.3
        score_posture = posture_ratio * 0.2
        score_emotion = (100 - avg_anxiety) * 0.2
        overall_score = score_conf + score_focus + score_posture + score_emotion

        print("\n" + "="*50)
        print(f"🎓 AI 면접 최종 분석 리포트 [{self.session_id}]")
        print("="*50)
        print(f"⏱️ 총 질문 수: {len(self.questions_history)}개")
        print(f"⏱️ 분석 시간: {int(time.time() - self.session_started_at)}초")
        print("-" * 50)
        print("🧮 상세 채점 내역 (Score Breakdown):")
        print(f"   1. 자신감(미소) : {avg_smile:5.1f}점 x 0.3 = {score_conf:4.1f}점")
        print(f"   2. 시선집중     : {gaze_ratio:5.1f}점 x 0.3 = {score_focus:4.1f}점")
        print(f"   3. 자세안정     : {posture_ratio:5.1f}점 x 0.2 = {score_posture:4.1f}점")
        print(f"   4. 정서안정     : {100-avg_anxiety:5.1f}점 x 0.2 = {score_emotion:4.1f}점")
        print(f"   -------------------------------------------")
        print(f"   ∑ 최종 합계: {overall_score:.1f}점")
        print("="*50 + "\n")

    async def process_vision(self, frame, timestamp_ms):
        try:
            img = frame.to_ndarray(format="bgr24")
            result = self.analyzer.process_frame(img, timestamp_ms)
            
            if result and result.get("status") == "detected":
                self.total_frames += 1
                q = self.current_q_data
                q["total_frames"] += 1
                q["smile_scores"].append(result["scores"]["smile"])
                q["anxiety_scores"].append(result["scores"]["anxiety"])
                if result["flags"]["is_center"]: q["gaze_center_frames"] += 1
                if result["flags"]["is_stable"]: q["posture_stable_frames"] += 1

                current_time = time.time()
                if current_time - self.last_log_time > 1.5:
                    self.last_log_time = current_time
                    labels = result["labels"]
                    logger.info(f"[{self.session_id}] Q{self.current_q_index} | 👀 시선: {labels['gaze']} | 👤 자세: {labels['posture']} | 😊 미소: {int(result['scores']['smile']*100)}%")

                ws = active_websockets.get(self.session_id)
                if ws:
                    await send_to_websocket(ws, {
                        "type": "vision_analysis",
                        "data": result,
                        "timestamp": current_time
                    })
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")

    async def recv(self):
        try:
            frame = await self.track.recv()
            current_time = time.time()
            if current_time - self.last_tracking_time > 0.1:
                self.last_tracking_time = current_time
                asyncio.create_task(self.process_vision(frame, int(current_time * 1000)))
            return frame
        except Exception:
            self.generate_final_report()
            raise

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
            # 클라이언트로부터 메시지 수신 대기
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # [추가] 질문 전환 신호 처리
                if msg.get("type") == "next_question":
                    new_idx = msg.get("index", 0)
                    # 해당 세션의 비디오 트랙을 찾아서 switch_question 호출
                    pc = active_pcs.get(session_id)
                    if pc:
                        for sender in pc.getSenders():
                            if isinstance(sender.track, VideoAnalysisTrack):
                                sender.track.switch_question(new_idx)
                                break
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        logger.info(f"[{session_id}] ❌ WebSocket 연결 종료")
    except Exception as e:
        logger.error(f"[{session_id}] WebSocket 에러: {e}")
    finally:
        if session_id in active_websockets:
            del active_websockets[session_id]
        if session_id in active_pcs:
            # PC는 별도로 닫히지 않았을 경우를 위해 유지하거나 종료 처리 고민
            # 여기서는 WebSocket 종료 시 PC도 정리하도록 구현
            pc = active_pcs.pop(session_id, None)
            if pc:
                await pc.close()
            logger.info(f"[{session_id}] 세션 리소스 정리 완료")

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
    active_pcs[session_id] = pc # [추가] 세션별 PC 저장
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