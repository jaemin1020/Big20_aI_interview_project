import base64
import numpy as np
import cv2
import time
import logging
from deepface import DeepFace
from celery import shared_task

logger = logging.getLogger("AI-Worker-Vision")

@shared_task(name="tasks.vision.analyze_emotion")
def analyze_emotion(session_id, base64_img):
    try:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid session_id type: {type(session_id)} - {session_id}")
            return {"error": "Invalid session ID format"}
            
        # 이미지 디코딩
        img_data = base64.b64decode(base64_img)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # DeepFace 분석
        results = DeepFace.analyze(
            img_path=img, 
            actions=['emotion'],
            detector_backend='opencv',
            enforce_detection=False
        )
        
        # JSON 결과 구성
        res = {
            "session_id": session_id,
            "type": "emotion",
            "dominant_emotion": results[0]['dominant_emotion'],
            "score": results[0]['emotion'][results[0]['dominant_emotion']]
        }
        
        # DB 업데이트 (세션의 최신 감정 상태 업데이트)
        from db import update_session_emotion
        update_session_emotion(session_id, res)
        
        logger.info(f"[{session_id}] Emotion analyzed and saved: {res['dominant_emotion']}")
        return res
    except Exception as e:
        logger.error(f"Vision Task Error: {str(e)}")
        return {"error": str(e)}

@shared_task(name="tasks.vision.track_eyes")
def track_eyes(session_id, base64_img):
    """
    눈 추적 및 시선 집중도 분석 Task (시각화 포함)
    OpenCV Haar Cascade를 사용하여 얼굴 ROI 내에서 눈을 감지하고 마킹
    """
    try:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            return {"error": "Invalid session ID format"}

        # 1. 이미지 디코딩
        img_data = base64.b64decode(base64_img)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. 얼굴 감지
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        eye_data = []
        status = "not_detected"

        for (x, y, w, h) in faces:
            # 시각화: 얼굴 영역 사각형 (Green)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # 얼굴 ROI 설정
            roi_gray = gray[y:y+h, x:x+w]
            
            # ROI 내에서 눈 감지
            eyes = eye_cascade.detectMultiScale(roi_gray)
            
            eyes_coords = []
            for (ex, ey, ew, eh) in eyes:
                # 전체 이미지 기준 좌표 변환
                # global_cx = x + ex + ew // 2
                
                eyes_coords.append({
                    "x": int(x + ex),
                    "y": int(y + ey),
                    "w": int(ew),
                    "h": int(eh)
                })
                
                # 시각화: 눈 영역 사각형 (Red)
                cv2.rectangle(img, (x + ex, y + ey), (x + ex + ew, y + ey + eh), (0, 0, 255), 2)
            
            # 눈이 2개 이상 감지되면 집중 상태로 간주
            if len(eyes) >= 2:
                status = "focused"
            elif len(eyes) == 1:
                status = "partially_detected"
            else:
                status = "eyes_not_visible"

            eye_data.append({
                "face_rect": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "eyes": eyes_coords,
                "status": status
            })
            
            # 가장 큰 얼굴 하나만 처리 (면접자)
            break
        
        # 3. 처리된 이미지 인코딩 (디버깅/모니터링용)
        # 이미지가 메모리 상에서 수정되었으므로 다시 인코딩
        _, buffer = cv2.imencode('.jpg', img)
        processed_base64 = base64.b64encode(buffer).decode('utf-8')
            
        res = {
            "session_id": session_id,
            "type": "eye_tracking",
            "data": eye_data,
            "status": status,
            "timestamp": time.time(),
            "debug_image": processed_base64  # 시각화된 이미지 반환
        }

        # DB 업데이트 
        from db import update_session_emotion
        # 이미지 데이터는 DB에 저장하지 않음 (용량 문제)
        db_data = res.copy()
        db_data.pop("debug_image", None)
        update_session_emotion(session_id, db_data)
        
        logger.info(f"[{session_id}] Eye tracking: {status}")
        return res

    except Exception as e:
        logger.error(f"Eye Tracking Error: {str(e)}")
        return {"error": str(e)}