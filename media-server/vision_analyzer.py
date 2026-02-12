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
        # 모델 경로
        self.model_path = 'model_repository/face_landmarker.task'
        
        self.detector = None
        self.is_ready = False

        # 모델 파일 존재 확인 및 다운로드
        if not os.path.exists(self.model_path):
            logger.warning(f"⚠️ 모델 파일 없음: {self.model_path}")
            try:
                logger.info("-> 모델 다운로드 시도 (urllib)...")
                os.makedirs("model_repository", exist_ok=True)
                import urllib.request
                url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
                urllib.request.urlretrieve(url, self.model_path)
                logger.info("✅ 모델 다운로드 완료")
            except Exception as e:
                logger.error(f"❌ 모델 다운로드 실패: {e}")
                return
            
        try:
            base_options = python.BaseOptions(
                model_asset_path=self.model_path,
                delegate=python.BaseOptions.Delegate.CPU # Docker 환경에서는 CPU 권장
            )
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True, # 표정 분석 활성화
                running_mode=vision.RunningMode.VIDEO, # 비디오 스트림 모드
                num_faces=1 # 면접자 1명만 분석
            )
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
        self.calibrated_eye_diff = 0.0
        self.calibrated_tilt_diff = 0.0
        
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
            blendshapes_list = result.face_blendshapes[0]
            
            # 1. 시선 분석 (Gaze)
            left_iris = landmarks[468] # 왼쪽 눈동자
            diff_x = left_iris.x - self.calibrated_gaze_x
            diff_y = left_iris.y - self.calibrated_gaze_y
            
            gaze_label = "정면 응시"
            if diff_x < -GAZE_TOLERANCE_X: gaze_label = "왼쪽 주시"
            elif diff_x > GAZE_TOLERANCE_X: gaze_label = "오른쪽 주시"
            elif diff_y < -GAZE_TOLERANCE_Y: gaze_label = "위쪽 주시"
            elif diff_y > GAZE_TOLERANCE_Y: gaze_label = "아래쪽 주시"
            
            # 2. 자세 분석 (Posture) - CV-V2-TASK.py 로직 보강
            # 눈 깊이 차이 (몸 비틀림), 눈 높이 차이 (갸우뚱)
            eye_diff = abs(landmarks[33].z - landmarks[263].z)
            tilt_diff = abs(landmarks[33].y - landmarks[263].y)
            nose_tip = landmarks[1]
            chin = landmarks[152]
            pitch_val = chin.z - nose_tip.z 
            
            # 영점 대비 오차 확인 (PoC 임계값 적용)
            is_posture_stable = abs(eye_diff - self.calibrated_eye_diff) < 0.04 and \
                               abs(tilt_diff - self.calibrated_tilt_diff) < 0.03
            is_head_straight = abs(pitch_val - self.calibrated_pitch) < HEAD_SENSITIVITY
            
            posture_label = "안정"
            if not is_posture_stable: posture_label = "자세 불균형"
            elif not is_head_straight: posture_label = "고개 각도 이탈"

            # 3. 감정 분석 (Blendshapes)
            bs_map = {b.category_name: b.score for b in blendshapes_list}
            smile_score = (bs_map.get('mouthSmileLeft', 0) + bs_map.get('mouthSmileRight', 0)) / 2
            brow_down_score = (bs_map.get('browDownLeft', 0) + bs_map.get('browDownRight', 0)) / 2
            
            emotion_label = "평온"
            if brow_down_score > 0.35: emotion_label = "긴장"
            elif smile_score > 0.4: emotion_label = "자신감"
            
            return {
                "status": "detected",
                "labels": {
                    "gaze": gaze_label,
                    "posture": posture_label,
                    "emotion": emotion_label
                },
                "scores": {
                    "smile": round(smile_score, 3),
                    "anxiety": round(brow_down_score, 3),
                    "pitch": round(pitch_val, 4),
                    "eye_diff": round(eye_diff, 4),
                    "tilt_diff": round(tilt_diff, 4)
                },
                "flags": {
                    "is_center": gaze_label == "정면 응시",
                    "is_stable": posture_label == "안정"
                }
            }
            
        except Exception as e:
            logger.error(f"비전 분석 중 에러: {e}")
            return None

    def close(self):
        if self.detector:
            self.detector.close()
