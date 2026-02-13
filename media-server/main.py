import os
import sys

# [DEBUG] 서버 시작 즉시 출력 (버퍼링 방지용 flush=True)
print("🚀 [Media-Server] Starting module initialization...", flush=True)

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

# 비전 분석기 전역 변수
analyzer_instance = None

def get_analyzer():
    global analyzer_instance
    if analyzer_instance is None:
        print("🚀 [Media-Server] VisionAnalyzer first access - initializing (Lazy)...", flush=True)
        analyzer_instance = VisionAnalyzer()
    return analyzer_instance

async def background_init_analyzer():
    """서버 시작 시 백그라운드 스레드에서 모델 미리 로딩 (Non-blocking)"""
    global analyzer_instance
    try:
        print("🚀 [Media-Server] Background VisionAnalyzer initialization started...", flush=True)
        # 블로킹 오퍼레이션을 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        analyzer_instance = await loop.run_in_executor(None, VisionAnalyzer)
        print("✅ [Media-Server] Background VisionAnalyzer initialization complete!", flush=True)
    except Exception as e:
        print(f"❌ [Media-Server] Background initialization failed: {e}", flush=True)

# 2. Celery 설정
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("ai_worker", broker=redis_url, backend=redis_url)

# 3. 연결 관리 (세션별 WebSocket 및 PeerConnection 저장)
active_websockets: Dict[str, WebSocket] = {}
active_pcs: Dict[str, RTCPeerConnection] = {}
active_video_tracks: Dict[str, 'VideoAnalysisTrack'] = {}

class VideoAnalysisTrack(MediaStreamTrack):
    """비디오 프레임을 추출하여 ai-worker에 감정 분석을 요청하는 트랙"""
    kind = "video"

    def __init__(self, track, session_id):
        super().__init__()
        self.track = track
        self.session_id = session_id
        
        # [데이터 누적용] 지연 로딩 호출
        self.analyzer = get_analyzer()
        self.session_started_at = time.time()
        self.total_frames = 0
        
        # 질문별 데이터 (전체 합산을 위해 리스트로 관리)
        self.questions_history = [] 
        self.current_q_index = 0
        self.current_q_data = self._get_empty_q_data()
        
        # [신규] 전체 면접 통합 데이터 버켓 (모든 프레임 누적)
        self.session_all_data = self._get_empty_q_data()
        
        # 실시간 로그 쿨타임
        self.last_log_time = 0
        self.last_tracking_time = 0
        
        print(f"✅ [{session_id}] VideoAnalysisTrack Created (Continuous Analysis Mode)")

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
        # [변경] 중간 리포트 출력은 생략하고 데이터만 백업
        if self.current_q_data["total_frames"] > 0:
            self.questions_history.append(self.current_q_data)
        
        self.current_q_index = new_index
        self.current_q_data = self._get_empty_q_data()
        print(f"➡️ [{self.session_id}] Moved to Question {new_index} (Continuous tracking...)", flush=True)

    def _calculate_scores(self, q_list):
        """질문 리스트(또는 단일 질문)로부터 POC 가중치 기반 점수 계산"""
        if not q_list: return None
        if isinstance(q_list, dict): q_list = [q_list]
        
        total_frames = sum(q["total_frames"] for q in q_list)
        if total_frames == 0: return None

        all_smiles = []
        all_anxiety = []
        total_gaze_center = 0
        total_posture_stable = 0
        
        for q in q_list:
            all_smiles.extend(q["smile_scores"])
            all_anxiety.extend(q["anxiety_scores"])
            total_gaze_center += q["gaze_center_frames"]
            total_posture_stable += q["posture_stable_frames"]

        # [보정] POC 수식은 너무 엄격함 (미소가 0이면 자신감 0점 처리됨)
        # 면접 문맥에 맞게 보정: (평균 점수 * 0.6) + 40 (기본 40점 베이스)
        
        # 1. 자신감 (미소): 무표정(0%)일 때 40점, 활짝(100%)일 때 100점
        adj_smile = (avg_smile * 0.6) + 40
        score_conf = adj_smile * 0.3
        
        # 2. 시선집중: 정면 응시 비율에 따라 40~100점
        adj_focus = (gaze_ratio * 0.6) + 40
        score_focus = adj_focus * 0.3
        
        # 3. 자세안정: 40~100점
        adj_posture = (posture_ratio * 0.6) + 40
        score_posture = adj_posture * 0.2
        
        # 4. 정서안정: 긴장도(anxiety)가 0일 때 100점, 100일 때 40점
        adj_emotion = ((100 - avg_anxiety) * 0.6) + 40
        score_emotion = adj_emotion * 0.2
        
        overall_score = score_conf + score_focus + score_posture + score_emotion
        
        return {
            "avg_smile": adj_smile, "avg_anxiety": avg_anxiety,
            "gaze_ratio": adj_focus, "posture_ratio": adj_posture,
            "raw_smile": avg_smile, "raw_focus": gaze_ratio, # 디버깅용 원본값
            "score_conf": score_conf, "score_focus": score_focus,
            "score_posture": score_posture, "score_emotion": score_emotion,
            "overall_score": overall_score, "total_frames": total_frames
        }

    def _log_question_summary(self):
        """질문별 상세 채점 리포트 로그 출력 (POC 디자인)"""
        s = self._calculate_scores(self.current_q_data)
        if not s: return
        
        print("\n" + "-"*50)
        print(f"📝 AI 면접 [{self.current_q_index}번] 질문 분석 리포트")
        print("-" * 50)
        print(f"   1. 자신감(미소) : {s['avg_smile']:5.1f}점 x 0.3 = {s['score_conf']:4.1f}점")
        print(f"   2. 시선집중     : {s['gaze_ratio']:5.1f}점 x 0.3 = {s['score_focus']:4.1f}점")
        print(f"   3. 자세안정     : {s['posture_ratio']:5.1f}점 x 0.2 = {s['score_posture']:4.1f}점")
        print(f"   4. 정서안정     : {100-s['avg_anxiety']:5.1f}점 x 0.2 = {s['score_emotion']:4.1f}점")
        print(f"   -------------------------------------------")
        print(f"   ∑ 해당 질문 합계: {s['overall_score']:.1f}점")
        print("-" * 50 + "\n")

    def generate_final_report(self):
        """면접 종료 시 전체 합산 리포트 로그 출력 (POC 디자인)"""
        # [변경] 모든 프레임이 이미 session_all_data에 모여있으므로 이를 기반으로 계산
        s = self._calculate_scores(self.session_all_data)
        if not s: 
            print(f"⚠️ [{self.session_id}] No analysis data captured during session.")
            return

        print("\n" + "="*50)
        print(f"🏆 AI 면접 [최종 종합] 분석 리포트 [{self.session_id}]")
        print("="*50)
        print(f"⏱️ 총 질문 수: {len(self.questions_history) + 1}개")
        print(f"⏱️ 분석 기간: {int(time.time() - self.session_started_at)}초 / {s['total_frames']} frames")
        print("-" * 50)
        print("🧮 [Holistic Capture] 전체 평균 채점 내역:")
        print(f"   1. 자신감(미소) : {s['avg_smile']:5.1f}점 x 0.3 = {s['score_conf']:4.1f}점")
        print(f"   2. 시선집중     : {s['gaze_ratio']:5.1f}점 x 0.3 = {s['score_focus']:4.1f}점")
        print(f"   3. 자세안정     : {s['posture_ratio']:5.1f}점 x 0.2 = {s['score_posture']:4.1f}점")
        print(f"   4. 정서안정     : {100-s['avg_anxiety']:5.1f}점 x 0.2 = {s['score_emotion']:4.1f}점")
        print(f"   -------------------------------------------")
        print(f"   ∑ 최종 종합 합계: {s['overall_score']:.1f}점")
        print("="*50 + "\n")

    async def process_vision(self, frame, timestamp_ms):
        if not self.analyzer.is_ready:
            print(f"⚠️ [{self.session_id}] Vision Analyzer NOT READY", flush=True)
            return

        try:
            # print(f"[{self.session_id}] Processing frame at {timestamp_ms}", flush=True)
            img = frame.to_ndarray(format="bgr24")
            result = self.analyzer.process_frame(img, timestamp_ms)
            
            if result and result.get("status") == "detected":
                self.total_frames += 1
                
                # 1. 현재 질문 데이터 누적
                q = self.current_q_data
                q["total_frames"] += 1
                q["smile_scores"].append(result["scores"]["smile"])
                q["anxiety_scores"].append(result["scores"]["anxiety"])
                if result["flags"]["is_center"]: q["gaze_center_frames"] += 1
                if result["flags"]["is_stable"]: q["posture_stable_frames"] += 1

                # 2. [변경] 전체 세션 데이터에도 통합 누적
                a = self.session_all_data
                a["total_frames"] += 1
                a["smile_scores"].append(result["scores"]["smile"])
                a["anxiety_scores"].append(result["scores"]["anxiety"])
                if result["flags"]["is_center"]: a["gaze_center_frames"] += 1
                if result["flags"]["is_stable"]: a["posture_stable_frames"] += 1

                # [DEBUG] 첫 프레임 수신 시 로그
                if self.total_frames == 1:
                    print(f"📊 [{self.session_id}] Video capture started (Analyzing whole session...)", flush=True)

                current_time = time.time()
                if current_time - self.last_log_time > 1.5:
                    self.last_log_time = current_time
                    labels = result["labels"]
                    print(f"[{self.session_id}] Q{self.current_q_index} | 👀 시선: {labels['gaze']} | 👤 자세: {labels['posture']} | 😊 미소: {int(result['scores']['smile']*100)}%")

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
        # MediaStreamTrack 서브클래싱 유지 (이후 필요 시 확장을 위해)
        return await self.track.recv()

async def start_video_analysis(track, session_id):
    """비디오 트랙을 직접 소비하며 분석하는 백그라운드 루프 (강제 프레임 수신)"""
    print(f"🎬 [{session_id}] Video analysis background loop STARTED", flush=True)
    analysis_track = VideoAnalysisTrack(track, session_id)
    active_video_tracks[session_id] = analysis_track
    
    try:
        while True:
            frame = await track.recv()
            curr = time.time()
            # 10FPS (0.1s 간격) 분석
            if curr - analysis_track.last_tracking_time > 0.1:
                analysis_track.last_tracking_time = curr
                asyncio.create_task(analysis_track.process_vision(frame, int(curr * 1000)))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"⚠️ [{session_id}] Video analysis loop error: {e}", flush=True)
    finally:
        print(f"🏁 [{session_id}] Video analysis loop FINISHED", flush=True)
        if analysis_track.current_q_data["total_frames"] > 0:
            analysis_track._log_question_summary()
        analysis_track.generate_final_report()
        active_video_tracks.pop(session_id, None)

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
                    # [변경] active_video_tracks에서 직접 트랙 찾기
                    video_track = active_video_tracks.get(session_id)
                    if video_track:
                        video_track.switch_question(new_idx)
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
            # 비디오 트랙: 백그라운드 분석 루프 시작 (addTrack 대신 직접 소비)
            asyncio.ensure_future(start_video_analysis(relay.subscribe(track), session_id))
            logger.info(f"[{session_id}] Video analysis loop scheduled")

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

@app.on_event("startup")
async def on_startup():
    print("🚀 [Media-Server] FastAPI startup complete. Port 8080 is now open.", flush=True)
    # 서버 기동 직후 백그라운드에서 모델 로딩 시작 (비블로킹)
    asyncio.create_task(background_init_analyzer())

@app.get("/status")
async def status():
    is_ready = analyzer_instance.is_ready if analyzer_instance else False
    return {
        "status": "running",
        "vision_analyzer_ready": is_ready,
        "session_count": len(active_pcs)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")