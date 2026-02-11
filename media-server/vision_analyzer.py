import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import logging
import os

logger = logging.getLogger("Vision-Analyzer")

# [설정] PoC와 동일한 분석 민감도 (상수)
GAZE_TOLERANCE_X = 0.08  # 시선 좌우 허용치
GAZE_TOLERANCE_Y = 0.08  # 시선 상하 허용치
HEAD_SENSITIVITY = 0.008 # 고개 끄덕임 민감도

class VisionAnalyzer:
    """
    미디어 서버용 MediaPipe 비전 분석기
    (화면 그리기 기능 제거, 순수 데이터 분석용)
    """
    def __init__(self):
        # 모델 경로 (Docker 환경에 맞게 수정 필요)
        # 현재 경로: /app (media-server root)
        # 모델은 미리 다운로드 되어 있어야 함
        self.model_path = 'model_repository/face_landmarker.task'
        
        self.detector = None
        self.is_ready = False

        # 모델 파일 존재 확인
        if not os.path.exists(self.model_path):
            logger.warning(f"⚠️ 모델 파일 없음: {self.model_path}")
            # 컨테이너 내에서 모델 다운로드 시도 (curl)
            try:
                logger.info("-> Google 서버에서 모델 다운로드 시도...")
                os.makedirs("model_repository", exist_ok=True)
                os.system(f"curl -L -o {self.model_path} https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
            except Exception as e:
                logger.error(f"모델 다운로드 실패: {e}")
                return
            
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True, # 표정 분석 활성화
                running_mode=vision.RunningMode.VIDEO, # 비디오 스트림 모드
                num_faces=1 # 면접자 1명만 분석
            )
            # 모델 로드
            self.detector = vision.FaceLandmarker.create_from_options(options)
            logger.info("✅ MediaPipe FaceLandmarker 로드 완료")
            self.is_ready = True
        except Exception as e:
            logger.error(f"❌ Vision 모델 로드 실패: {e}")
            self.is_ready = False

        # 영점 (Calibration) 기본값 (PoC와 동일)
        self.calibrated_gaze_x = 0.43
        self.calibrated_gaze_y = 0.36
        self.calibrated_pitch = 0.05
        
    def process_frame(self, frame_bgr, timestamp_ms):
        """
        비디오 프레임(BGR)을 받아 분석 결과(Dict)를 반환
        """
        if not self.is_ready:
            return None

        # OpenCV(BGR) -> MediaPipe(RGB) 변환
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        try:
            # AI 추론 실행
            result = self.detector.detect_for_video(mp_image, int(timestamp_ms))
            
            if not result.face_landmarks:
                return {"status": "not_detected"}
                
            landmarks = result.face_landmarks[0]
            blendshapes = result.face_blendshapes[0]
            
            # 1. 시선 분석 (Gaze)
            left_iris = landmarks[468] # 왼쪽 눈동자
            diff_x = left_iris.x - self.calibrated_gaze_x
            diff_y = left_iris.y - self.calibrated_gaze_y
            
            gaze_status = "center"
            if diff_x < -GAZE_TOLERANCE_X: gaze_status = "left"
            elif diff_x > GAZE_TOLERANCE_X: gaze_status = "right"
            elif diff_y < -GAZE_TOLERANCE_Y: gaze_status = "up"
            elif diff_y > GAZE_TOLERANCE_Y: gaze_status = "down"
            
            # 2. 자세 분석 (Head Pose)
            nose_tip = landmarks[1]
            chin = landmarks[152]
            pitch_val = chin.z - nose_tip.z # 고개 끄덕임
            head_status = "stable" if abs(pitch_val - self.calibrated_pitch) < HEAD_SENSITIVITY else "unstable"
            
            # 3. 감정 분석 (Blendshapes)
            # 결과를 딕셔너리로 변환
            bs_map = {b.category_name: b.score for b in blendshapes}
            
            # 주요 지표 추출
            smile_score = (bs_map.get('mouthSmileLeft', 0) + bs_map.get('mouthSmileRight', 0)) / 2
            brow_down_score = (bs_map.get('browDownLeft', 0) + bs_map.get('browDownRight', 0)) / 2
            
            emotion_label = "neutral"
            if smile_score > 0.4: emotion_label = "happy"
            if brow_down_score > 0.4: emotion_label = "anxious" # 긴장/찌푸림
            
            return {
                "status": "detected",
                "gaze": gaze_status,       # center, left, right...
                "head": head_status,       # stable, unstable
                "emotion": emotion_label,  # neutral, happy, anxious
                "scores": {
                    "smile": round(smile_score, 3),
                    "anxiety": round(brow_down_score, 3),
                    "gaze_x": round(diff_x, 3),
                    "gaze_y": round(diff_y, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"비전 분석 중 에러: {e}")
            return None

    def close(self):
        if self.detector:
            self.detector.close()
