import os
import sys

# [로그] 서버 시작 즉시 출력 (버퍼링 방지용 flush=True)
print("🚀 [미디어 서버] 모듈 초기화 시작 중...", flush=True)

import asyncio
import json
import logging

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

# [Global Monkey Patch] Force UDP Port Range for Docker NAT Traversal
# aiortc/aioice는 기본적으로 random port(0)를 사용하므로, 이를 Docker가 매핑한 50000-50050 범위로 강제함
import socket
import random

original_socket_bind = socket.socket.bind

def restricted_socket_bind(self, address):
    # UDP 소켓이고, 포트가 0(랜덤)일 경우에만 개입
    if self.type == socket.SOCK_DGRAM and address[1] == 0:
        min_port = 50000
        max_port = 50050
        # 범위 내에서 랜덤 포트 시도 (최대 50번)
        for _ in range(100):
            try:
                port = random.randint(min_port, max_port)
                new_address = (address[0], port)
                original_socket_bind(self, new_address)
                print(f"✅ [MonkeyPatch] UDP Port Bound: {port}", flush=True)
                return
            except OSError:
                continue
        # 실패 시 원래대로 0으로 시도 (어차피 안 되겠지만)
        print("⚠️ [MonkeyPatch] UDP Port binding failed in range 50000-50050", flush=True)
        return original_socket_bind(self, address)
    
    # TCP거나 특정 포트가 지정된 경우는 그대로 통과
    return original_socket_bind(self, address)

socket.socket.bind = restricted_socket_bind
print("🐒 [미디어 서버] Global Socket Monkey Patch Applied: UDP Ports 50000-50050", flush=True)

# 1. 로깅 설정
# [필수] WebRTC 디버깅 로그 (연결 문제 해결용)
# 너무 시끄러우면 WARNING으로 변경
logging.basicConfig(level=logging.INFO) # 전체 레벨은 INFO로 유지
logger = logging.getLogger("Media-Server")

# aiortc 및 aioice 로그 레벨 조정 (연결 성공했으므로 시끄러운 로그 숨김)
logging.getLogger("aiortc").setLevel(logging.WARNING)
logging.getLogger("aioice").setLevel(logging.WARNING)
logging.getLogger("av").setLevel(logging.WARNING) # av 라이브러리 로그도 숨김

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
        print("🚀 [미디어 서버] 분석 엔진(VisionAnalyzer) 첫 접근 - 초기화 중 (지연 로딩)...", flush=True)
        analyzer_instance = VisionAnalyzer()
    return analyzer_instance

async def background_init_analyzer():
    """서버 시작 시 백그라운드 스레드에서 모델 미리 로딩 (Non-blocking)"""
    global analyzer_instance
    try:
        print("🚀 [미디어 서버] 백그라운드 분석 엔진 초기화 시작...", flush=True)
        # 블로킹 오퍼레이션을 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        analyzer_instance = await loop.run_in_executor(None, VisionAnalyzer)
        print("✅ [미디어 서버] 백그라운드 분석 엔진 초기화 완료!", flush=True)
    except Exception as e:
        print(f"❌ [미디어 서버] 백그라운드 초기화 실패: {e}", flush=True)

# 2. Celery 설정
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("ai_worker", broker=redis_url, backend=redis_url)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    redis_backend_health_check_interval=30,  # 연결 안정성 확보
)

# 3. 연결 관리 (세션별 WebSocket 및 PeerConnection 저장)
active_websockets: Dict[str, WebSocket] = {}
active_pcs: Dict[str, RTCPeerConnection] = {}
active_video_tracks: Dict[str, 'VideoAnalysisTrack'] = {}
active_analysis_tasks: Dict[str, asyncio.Task] = {}
ws_locks: Dict[str, asyncio.Lock] = {} # [추가] 웹소켓 동시 전송 방지용 락

async def send_to_websocket(session_id: str, data: dict):
    """WebSocket으로 데이터 전송 (Lock을 사용하여 동시 전송 충돌 방지)"""
    ws = active_websockets.get(session_id)
    if not ws:
        return
    
    # 세션별 락 가져오기
    if session_id not in ws_locks:
        ws_locks[session_id] = asyncio.Lock()
    
    async with ws_locks[session_id]:
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.error(f"[{session_id}] WebSocket 전송 실패: {e}")
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
        
        # [DEBUG] 생성 완료 로그
        print(f"✅ [{session_id}] VideoAnalysisTrack 초기화 완료 (Analyzer: {self.analyzer is not None})", flush=True)

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
        print(f"➡️ [{self.session_id}] {new_index}번 질문으로 전환됨 (연속 추적 중...)", flush=True)

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

        # [계산] 평균값 산출 (0으로 나누기 방지)
        if not all_smiles: avg_smile = 0.0
        else: avg_smile = (sum(all_smiles) / len(all_smiles)) * 100  # 0~1 -> 0~100점 환산
        
        if not all_anxiety: avg_anxiety = 0.0
        else: avg_anxiety = (sum(all_anxiety) / len(all_anxiety)) * 100 # 0~1 -> 0~100점 환산
        
        gaze_ratio = (total_gaze_center / total_frames) * 100
        posture_ratio = (total_posture_stable / total_frames) * 100

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
            print(f"⚠️ [{self.session_id}] 세션 동안 분석된 데이터가 없습니다.")
            return

        print("\n" + "="*50)
        print(f"🏆 AI 면접 [최종 종합] 분석 리포트 [{self.session_id}]")
        print("="*50)
        print(f"⏱️ 총 질문 수: {len(self.questions_history) + 1}개")
        print(f"⏱️ 분석 기간: {int(time.time() - self.session_started_at)}초 / {s['total_frames']} frames")
        print("-" * 50)
        print("🧮 [영상분석] 전체 평균 채점 내역:")
        print(f"   1. 자신감(미소) : {s['avg_smile']:5.1f}점 x 0.3 = {s['score_conf']:4.1f}점")
        print(f"   2. 시선집중     : {s['gaze_ratio']:5.1f}점 x 0.3 = {s['score_focus']:4.1f}점")
        print(f"   3. 자세안정     : {s['posture_ratio']:5.1f}점 x 0.2 = {s['score_posture']:4.1f}점")
        print(f"   4. 정서안정     : {100-s['avg_anxiety']:5.1f}점 x 0.2 = {s['score_emotion']:4.1f}점")
        print(f"   -------------------------------------------")
        print(f"   ∑ 최종 종합 합계: {s['overall_score']:.1f}점")
        print("="*50 + "\n")

    async def process_vision(self, frame, timestamp_ms):
        if not self.analyzer.is_ready:
            print(f"⚠️ [{self.session_id}] 분석 엔진이 아직 준비되지 않았습니다.", flush=True)
            return

        try:
            # print(f"[{self.session_id}] Processing frame at {timestamp_ms}", flush=True)
            img = frame.to_ndarray(format="bgr24")
            
            # [최적화] CPU 집약적 작업(MediaPipe)을 스레드 풀로 위임하여 이벤트 루프 차단 방지
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.analyzer.process_frame, img, timestamp_ms)
            
            if result and result.get("status") == "detected":
                self.total_frames += 1
                
                # 1. 현재 질문 데이터 누적
                q = self.current_q_data
                q["total_frames"] += 1
                q["smile_scores"].append(result["scores"]["smile"])
                q["anxiety_scores"].append(result["scores"]["anxiety"])
                if result["flags"]["is_center"]: q["gaze_center_frames"] += 1
                if result["flags"]["is_stable"]: q["posture_stable_frames"] += 1

                # 2. 전체 세션 데이터에도 통합 누적
                a = self.session_all_data
                a["total_frames"] += 1
                a["smile_scores"].append(result["scores"]["smile"])
                a["anxiety_scores"].append(result["scores"]["anxiety"])
                if result["flags"]["is_center"]: a["gaze_center_frames"] += 1
                if result["flags"]["is_stable"]: a["posture_stable_frames"] += 1

                # [DEBUG] 첫 프레임 수신 시 로그
                if self.total_frames == 1:
                    print(f"📊 [{self.session_id}] 영상 캡처 시작 (전체 세션 분석 중...)", flush=True)

                current_time = time.time()
                # [수정] 감지된 경우에도 2초마다 웹소켓 전송 (HUD 업데이트용)
                if current_time - self.last_log_time > 2.0:
                    self.last_log_time = current_time
                    s = self._calculate_scores(self.session_all_data)
                    labels = result["labels"]
                    # [사용자 컨펌용 로그]
                    print(f"[{self.session_id}] {self.current_q_index}번 질문 | [실시간 종합점수: {s['overall_score']:5.1f}점] | 👀 시선: {labels['gaze']:8} | 👤 자세: {labels['posture']:12} | 😊 미소: {int(result['scores']['smile']*100):3}%", flush=True)
                    
                    # [추가] 실시간 HUD 데이터 전송
                    await send_to_websocket(self.session_id, {
                        "type": "vision_analysis",
                        "data": {
                            "gaze": result["flags"]["is_center"], # 프론트엔드 기대 포맷으로 가공
                            "posture": result["labels"]["posture"],
                            "emotion": result["labels"]["emotion"],
                            "scores": result["scores"]
                        }
                    })
            else:
                # 얼굴 미감지 시에도 5초마다 로그 출력
                current_time = time.time()
                if current_time - self.last_log_time > 5.0:
                    self.last_log_time = current_time
                    status = result.get("status", "unknown") if result else "no_result"
                    print(f"❓ [{self.session_id}] 얼굴 인식 대기 중... (상태: {status})", flush=True)

                    await send_to_websocket(self.session_id, {
                        "type": "vision_analysis",
                        "data": result if result else {"status": "not_detected"},
                        "timestamp": current_time
                    })
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")

    async def recv(self):
        # MediaStreamTrack 서브클래싱 유지 (이후 필요 시 확장을 위해)
        return await self.track.recv()

async def start_video_analysis(track, session_id):
    """비디오 트랙을 직접 소비하며 분석하는 백그라운드 루프 (강제 프레임 수신)"""
    # [DEBUG] Track 정보 출력
    print(f"🎬 [{session_id}] 영상 분석 루프 진입: Track Kind={track.kind}, ID={track.id}, State={track.readyState}", flush=True)
    
    # Track 객체 생성 (이 부분이 오래 걸릴 수 있으므로 로그로 감쌈)
    try:
        print(f"⚙️ [{session_id}] VideoAnalysisTrack 객체 생성 시도...", flush=True)
        analysis_track = VideoAnalysisTrack(track, session_id)
        active_video_tracks[session_id] = analysis_track
        print(f"⚙️ [{session_id}] VideoAnalysisTrack 객체 생성 성공!", flush=True)
    except Exception as e:
        print(f"❌ [{session_id}] VideoAnalysisTrack 생성 실패: {e}", flush=True)
        return

    frame_count = 0
    try:
        while True:
            try:
                # [DEBUG] recv 대기 상태 로그 (너무 자주 찍히지 않도록 frame_count 0일 때만)
                if frame_count == 0:
                    print(f"⏳ [{session_id}] 첫 프레임 수신 대기 중...", flush=True)

                # 5초 타임아웃으로 프레임 수신 대기 (무한 대기 방지)
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                frame_count += 1
                curr = time.time()
                
                # [HEARTBEAT] 첫 프레임 및 100프레임마다 로그
                if frame_count == 1:
                    print(f"🎉 [{session_id}] 첫 프레임 수신 성공!", flush=True)
                if frame_count % 100 == 0:
                    print(f"📽️ [{session_id}] 현재까지 {frame_count} 프레임 수신됨...", flush=True)

                # [성능 조절] 5FPS (0.2s 간격) 분석 
                # (LLM 질문 생성 속도 저하 방지를 위해 분석 부하 감소)
                if curr - analysis_track.last_tracking_time > 0.2:
                    analysis_track.last_tracking_time = curr
                    asyncio.create_task(analysis_track.process_vision(frame, int(curr * 1000)))

            except asyncio.TimeoutError:
                print(f"⏰ [{session_id}] 5초간 프레임 수신 없음 (타임아웃)", flush=True)
                # 타임아웃 발생해도 루프는 계속 유지 (일시적 네트워크 지연일 수 있음)
                continue
    except asyncio.CancelledError:
        print(f"🛑 [{session_id}] 영상 분석 루프 취소됨", flush=True)
    except Exception as e:
        print(f"⚠️ [{session_id}] 영상 분석 루프 에러: {e}", flush=True)
    finally:
        print(f"🏁 [{session_id}] 영상 분석 루프 종료됨", flush=True)
        if analysis_track.current_q_data["total_frames"] > 0:
            analysis_track._log_question_summary()
        analysis_track.generate_final_report()
        active_video_tracks.pop(session_id, None)


async def send_to_websocket(ws: WebSocket, data: dict):
    """WebSocket으로 데이터 전송"""
    try:
        await ws.send_json(data)
    except Exception as e:
        logger.error(f"WebSocket 전송 실패: {e}")

# ============== WebSocket 엔드포인트 ==============

# STT 중계 함수 (Remote STT)
# WebRTC 오디오 스트림 -> WAV 파일 변환 -> AI Worker로 전송
async def start_remote_stt(track, session_id):
    logger.info(f"[{session_id}] 🎙️ 원격 STT 시작 (Remote STT Started)")
    
    # 약 2초 단위로 오디오를 모아서 전송 (Responsiveness 향상)
    CHUNK_THRESHOLD = 100 # 약 2초 (20ms * 100 = 2000ms)
    accumulated_frames = []
    
    try:
        while True:
            # 1. 오디오 프레임 수신
            frame = await track.recv()
            accumulated_frames.append(frame)
            
            if len(accumulated_frames) >= CHUNK_THRESHOLD:
                
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
                # [개선] 결과를 기다렸다가(브라우저가 아닌 서버가 기다림) 웹소켓으로 즉시 중계
                task = celery_app.send_task(
                    "tasks.stt.recognize",
                    args=[audio_b64],
                    queue="cpu_queue"
                )
                
                # 비대기(Non-blocking) 방식으로 결과를 받아 전송
                async def wait_and_relay(celery_task, sid):
                    try:
                        loop = asyncio.get_event_loop()
                        
                        # 최대 15초 동안 결과 추적 (큐 대기 시간 고려)
                        start_time = time.time()
                        is_ready = False
                        while time.time() - start_time < 15:
                            is_ready = await loop.run_in_executor(None, celery_task.ready)
                            if is_ready:
                                break
                            await asyncio.sleep(0.5) 
                        
                        if is_ready:
                            result = await loop.run_in_executor(None, lambda: celery_task.result)
                            if result and result.get("status") == "success":
                                text = result.get("text", "").strip()
                                if text:
                                    await send_to_websocket(sid, {
                                        "type": "stt_result",
                                        "text": text
                                    })
                                    logger.info(f"[{sid}] 🎤 실시간 자막 전송 성공: {text[:30]}...")
                    except Exception as e:
                        if "closed file" not in str(e).lower():
                            logger.error(f"[{sid}] STT 결과 중계 실패: {e}")
                    finally:
                        try:
                            celery_task.forget()
                        except:
                            pass

                # 결과 대기 루틴 실행
                asyncio.create_task(wait_and_relay(task, session_id))
                
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
        
        # [추가] 좀비 분석 루프 강제 종료
        analysis_task = active_analysis_tasks.pop(session_id, None)
        if analysis_task and not analysis_task.done():
            print(f"🛑 [{session_id}] 웹소켓 종료로 인한 영상 분석 루프 강제 취소...", flush=True)
            analysis_task.cancel()
            try:
                await analysis_task
            except asyncio.CancelledError:
                print(f"✅ [{session_id}] 영상 분석 루프 취소 완료", flush=True)

# ============== WebRTC 엔드포인트 ==============
def force_localhost_candidate(sdp_str):
    """
    Docker 환경에서 내부 IP(172.x.x.x)를 Host IP(127.0.0.1)로 변환하여
    클라이언트가 포트 포워딩을 통해 접속할 수 있도록 함.
    Regex를 사용하여 안전하게 치환 (파싱 에러 방지)
    """
    import re
    # 1. 172.16.x.x ~ 172.31.x.x (Docker Bridge)
    # \b 문자를 사용하여 IP 주소의 경계를 명확히 함 (오탐 방지)
    sdp_str = re.sub(r'\b172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}\b', '127.0.0.1', sdp_str)
    
    # 2. 10.x.x.x (Private)
    sdp_str = re.sub(r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '127.0.0.1', sdp_str)
    
    # 3. 192.168.x.x (Private)
    sdp_str = re.sub(r'\b192\.168\.\d{1,3}\.\d{1,3}\b', '127.0.0.1', sdp_str)
    
    return sdp_str

@app.post("/offer")
async def offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    session_id = str(params.get("session_id", "unknown")) # 무조건 문자열로 변환
    
    print(f"📨 [{session_id}] Received Offer SDP (First 500 chars): {params['sdp'][:500]}...", flush=True)

    # [수정] 로컬 개발 환경 강제 (STUN 제거)
    # Docker NAT 이슈를 피하기 위해, 외부 STUN 서버를 쓰지 않고 
    # 오직 Host Candidate(로컬 IP)만 사용하여 연결을 시도함.
    # force_localhost_candidate가 127.0.0.1로 바꿔주므로, 브라우저는 로컬로 붙게 됨.
    pc = RTCPeerConnection()
    
    active_pcs[session_id] = pc # [추가] 세션별 PC 저장

    @pc.on("iceconnectionstatechange")
    async def on_ice_connection_state_change():
        print(f"❄️ [{session_id}] ICE Connection State: {pc.iceConnectionState}", flush=True)
        if pc.iceConnectionState == "failed":
            print(f"❌ [{session_id}] WebRTC 연결 실패 (방화벽/네트워크 문제 가능성)", flush=True)

    @pc.on("track")
    def on_track(track):
        # [변경] 로그 레벨 일관성
        print(f"🎯 [{session_id}] 트랙 수신됨: {track.kind}", flush=True)

        if track.kind == "audio":
            # [변경 내역: 2026-02-11]
            # 1. 이전 코드의 `start_stt_with_local_whisper` 함수는 정의되지 않아 서버 크래시를 유발했습니다.
            # 2. 미디어 서버에서 모델을 직접 돌리면 비디오 중계가 렉걸릴 수 있으므로,
            #    무거운 STT 작업은 전용 GPU 워커(AI-Worker)에게 위임(Delegate)합니다.
            asyncio.ensure_future(start_remote_stt(track, session_id))
            print(f"[{session_id}] 오디오 트랙 처리 시작 (AI-Worker를 통한 원격 STT)", flush=True)
            
        elif track.kind == "video":
            # 비디오 트랙: 백그라운드 분석 루프 시작 (addTrack 대신 직접 소비)
            # [변경] Relay 우회하고 트랙 직접 소비 (블로킹 이슈 디버깅)
            print(f"🔄 [{session_id}] 영상 분석 루프 스케줄링 시도...", flush=True)
            task = asyncio.create_task(start_video_analysis(track, session_id))
            active_analysis_tasks[session_id] = task  # [추가] 태스크 저장
            print(f"🔄 [{session_id}] 영상 분석 루프 스케줄링 완료 (Direct Track)", flush=True)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # [수정] Docker 환경을 위한 SDP IP 변조 (Masquerading)
    final_sdp = force_localhost_candidate(pc.localDescription.sdp)
    print(f"🔧 [{session_id}] SDP Localhost Patch Applied. Result (Candidate Line Only):\n" + 
          "\n".join([line for line in final_sdp.splitlines() if "a=candidate" in line]), flush=True)

    return {
        "sdp": final_sdp,
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
            queue="cpu_queue"
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
    # [중요] MonkeyPatch가 작동하려면 uvicorn이 uvloop 대신 asyncio 루프를 사용해야 할 수 있음.
    # Docker 환경에서 aiortc 소켓 바인딩을 보장하기 위해 명시적으로 설정.
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info", loop="asyncio")