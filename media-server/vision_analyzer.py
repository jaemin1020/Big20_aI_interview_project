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

        if not os.path.exists(self.model_path) or os.path.getsize(self.model_path) < 1000:
            logger.warning(f"⚠️ 모델 파일 없음 또는 손상됨: {self.model_path}")
            try:
                import urllib.request
                url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
                logger.info(f"-> Google 서버에서 모델 다운로드 시작: {url}")
                
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                urllib.request.urlretrieve(url, self.model_path)
                
                if os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 1000:
                    logger.info(f"✅ 모델 다운로드 성공")
                else:
                    raise Exception("다운로드된 파일이 유효하지 않음")
            except Exception as e:
                logger.error(f"❌ 모델 다운로드 실패: {e}")
                return
            
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True,
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1
            )
            self.detector = vision.FaceLandmarker.create_from_options(options)
            logger.info("✅ MediaPipe FaceLandmarker 로드 완료")
            self.is_ready = True
        except Exception as e:
            logger.error(f"❌ Vision 모델 로드 실패: {e}")
            self.is_ready = False

        # 영점 (Calibration) 기본값
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
            left_iris = landmarks[468] 
            diff_x = left_iris.x - self.calibrated_gaze_x
            diff_y = left_iris.y - self.calibrated_gaze_y
            
            gaze_status = "center"
            if abs(diff_x) > GAZE_TOLERANCE_X or abs(diff_y) > GAZE_TOLERANCE_Y:
                gaze_status = "distracted"
            
            # 2. 자세 및 태도 분석 (Posture & Attitude)
            nose_tip = landmarks[1]
            chin = landmarks[152]
            left_ear = landmarks[234]
            right_ear = landmarks[454]
            
            pitch = chin.z - nose_tip.z  # 상하
            yaw = left_ear.z - right_ear.z # 좌우 회전
            roll = left_ear.y - right_ear.y # 좌우 기울기
            
            posture_stable = abs(pitch - self.calibrated_pitch) < HEAD_SENSITIVITY
            attitude_status = "stable" if posture_stable and abs(yaw) < 0.05 else "unstable"
            
            # 3. 집중도 점수 (Focus Score: 0~100)
            focus_score = 100
            if gaze_status == "distracted": focus_score -= 40
            if attitude_status == "unstable": focus_score -= 30
            focus_score -= min(30, abs(diff_x) * 100 + abs(diff_y) * 100)
            focus_score = max(0, round(focus_score, 1))
            
            # 4. 감정 및 표정 분석 (Emotion)
            bs_map = {b.category_name: b.score for b in blendshapes}
            smile_score = (bs_map.get('mouthSmileLeft', 0) + bs_map.get('mouthSmileRight', 0)) / 2
            anxiety_score = (bs_map.get('browDownLeft', 0) + bs_map.get('browDownRight', 0)) / 2
            surprise_score = (bs_map.get('eyeWideLeft', 0) + bs_map.get('eyeWideRight', 0)) / 2
            
            emotion_label = "neutral"
            if smile_score > 0.4: emotion_label = "happy"
            elif anxiety_score > 0.4: emotion_label = "anxious"
            elif surprise_score > 0.4: emotion_label = "surprised"

            return {
                "status": "detected",
                "gaze": gaze_status,
                "posture": attitude_status,
                "emotion": emotion_label,
                "focus_score": focus_score,
                "scores": {
                    "smile": round(smile_score, 3),
                    "anxiety": round(anxiety_score, 3),
                    "surprise": round(surprise_score, 3),
                    "pitch": round(pitch, 4),
                    "yaw": round(yaw, 4),
                    "focus": focus_score
                }
            }
            
        except Exception as e:
            logger.error(f"비전 분석 중 에러: {e}")
            return None

    def close(self):
        if self.detector:
            self.detector.close()
