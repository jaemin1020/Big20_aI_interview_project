import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import os
from PIL import Image, ImageDraw, ImageFont

# 모델 파일 확인
model_path = 'face_landmarker.task'

def get_korean_font(size):
    try: return ImageFont.truetype("malgun.ttf", size)
    except: return ImageFont.load_default()

font_title = get_korean_font(30)
font_label = get_korean_font(25)
font_raw = get_korean_font(18)

def draw_korean_text(img, text, position, color, font=font_label):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

def analyze_emotions():
    print("🎯 감정 인식 정밀 검증 모드 가동...")
    
    if not os.path.exists(model_path):
        print("❌ 모델 파일이 없습니다.")
        return

    detector = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path),
        output_face_blendshapes=True,
        running_mode=vision.RunningMode.VIDEO
    ))
    
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = detector.detect_for_video(mp_image, int(time.time() * 1000))

        if result.face_blendshapes:
            # 47가지 미세 근육 점수 추출
            shapes = {b.category_name: b.score for b in result.face_blendshapes[0]}
            
            # [1. 행복] 기존 유지 (잘 작동함)
            happy_score = (shapes.get('mouthSmileLeft', 0) + shapes.get('mouthSmileRight', 0)) / 2
            
            # [2. 슬픔] 민감도 최적화 (밸런스 모드)
            mouth_frown = (shapes.get('mouthFrownLeft', 0) + shapes.get('mouthFrownRight', 0)) / 2
            brow_down = (shapes.get('browDownLeft', 0) + shapes.get('browDownRight', 0)) / 2
            sad_score = max(mouth_frown * 1.8, brow_down * 1.2) # 적절한 가중치로 조절
            
            # [3. 놀람/두려움]
            eye_wide = (shapes.get('eyeWideLeft', 0) + shapes.get('eyeWideRight', 0)) / 2
            brow_up = shapes.get('browInnerUp', 0)
            surprise_score = max(eye_wide, brow_up * 1.2) 
            
            # [4. 최종 판별]
            current_emotion = "평온 (Neutral)"
            color = (255, 255, 255)
            
            # 우선순위: 행복 > 놀람 > 슬픔 순으로 강한 신호 감지
            if happy_score > 0.35: 
                current_emotion = "행복 (Happy) 😊"
                color = (0, 255, 0)
            elif surprise_score > 0.25: 
                current_emotion = "놀람/두려움 (Surprise/Fear) 😲"
                color = (0, 255, 255)
            elif sad_score > 0.12: # 적절한 임계값 설정
                current_emotion = "슬픔 (Sad) 😢"
                color = (255, 50, 50)

            # UI 그리기
            overlay = frame.copy()
            cv2.rectangle(overlay, (20, 20), (500, 350), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

            frame = draw_korean_text(frame, "📊 감정 정밀 검증 시스템", (40, 40), (255, 255, 0), font=font_title)
            frame = draw_korean_text(frame, f"현재 감정: {current_emotion}", (40, 100), color)
            
            # 실시간 로우 데이터 바 (시각화)
            cv2.rectangle(frame, (40, 160), (40 + int(happy_score*300), 180), (0, 255, 0), -1)
            frame = draw_korean_text(frame, f"행복 지수: {int(happy_score*100)}%", (350, 155), (200, 200, 200), font=font_raw)
            
            cv2.rectangle(frame, (40, 210), (40 + int(sad_score*300), 230), (0, 0, 255), -1)
            frame = draw_korean_text(frame, f"슬픔 지수: {int(sad_score*100)}%", (350, 205), (200, 200, 200), font=font_raw)
            
            cv2.rectangle(frame, (40, 260), (40 + int(surprise_score*300), 280), (0, 255, 255), -1)
            frame = draw_korean_text(frame, f"놀람 지수: {int(surprise_score*100)}%", (350, 255), (200, 200, 200), font=font_raw)

            frame = draw_korean_text(frame, "힌트: 웃어보고, 슬퍼보고, 눈을 크게 떠보세요!", (40, 310), (150, 150, 150), font=font_raw)

        cv2.imshow('Emotion Precision Verifier', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    detector.close(); cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    analyze_emotions()
