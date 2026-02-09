import cv2  # OpenCV: 이미지 처리 및 카메라 제어를 위한 핵심 라이브러리
import mediapipe as mp  # MediaPipe: 구글의 AI 프레임워크 (얼굴, 손 인식 등)
from mediapipe.tasks import python  # MediaPipe의 파이썬 태스크 모듈
from mediapipe.tasks.python import vision  # 비전(Vision) 관련 태스크 (FaceLandmarker 등)
import numpy as np  # NumPy: 수치 계산 및 행렬 연산용
import time  # 시간 측정 (FPS 계산 및 타임라인 기록용)
import os  # 운영체제 경로 및 파일 제어용
import json  # 결과 리포트 저장을 위한 JSON 라이브러리
from PIL import Image, ImageDraw, ImageFont  # Pillow: 한글 텍스트 렌더링을 위한 이미지 처리 라이브러리

# ==========================================
# 🎓 AI Interviewer Vision System
# Version: V4.5 (Final Release)
# Date: 2026-02-05
# Description: 실시간 얼굴 랜드마크 분석 기반 AI 면접 코칭 시스템
# ==========================================

# ==========================================
# [Step 1] 사용자 설정 및 상수 정의 (Configuration)
# ==========================================
# 1-1. 시선 및 자세 판정 임계값 (민감도 설정)
GAZE_TOLERANCE_X = 0.08   # 시선이 좌우로 이만큼 벗어나면 '이탈'로 간주
GAZE_TOLERANCE_Y = 0.08   # 시선이 상하로 이만큼 벗어나면 '이탈'로 간주
HEAD_SENSITIVITY = 0.008  # 고개 숙임/들림 변화량 민감도 (작을수록 예민함)

# 1-2. 최종 리포트 점수 배점 (총합 1.0)
WEIGHT_CONFIDENCE = 0.3   # 자신감(미소) 비중: 30%
WEIGHT_FOCUS      = 0.3   # 시선 집중도 비중: 30%
WEIGHT_POSTURE    = 0.2   # 자세 안정성 비중: 20%
WEIGHT_EMOTION    = 0.2   # 정서 안정성 비중: 20%

# 1-3. 영점(Calibration) 초기값 설정
# 사용자가 's'키를 누르면 현재 자신의 위치로 이 값들이 갱신됩니다.
calibrated_gaze_x = 0.43   # 기준 눈동자 X 좌표
calibrated_gaze_y = 0.36   # 기준 눈동자 Y 좌표
calibrated_pitch = 0.05    # 기준 고개 각도 (Pitch)
calibrated_eye_diff = 0.0  # 기준 눈 높이 차이 (기울기)
calibrated_tilt_diff = 0.0 # 기준 얼굴 기울기

# 1-4. 세션 데이터 저장소 (Session Storage)
# 면접 진행 동안 발생하는 모든 데이터를 누적하는 딕셔너리입니다.
session_data = {
    "start_time": 0,           # 면접 시작 시간
    "total_frames": 0,         # 처리된 총 프레임 수
    "smile_scores": [],        # 매 프레임의 미소 점수 리스트
    "anxiety_scores": [],      # 매 프레임의 불안(미간) 점수 리스트
    "gaze_center_frames": 0,   # 시선이 정면이었던 프레임 수
    "posture_stable_frames": 0,# 자세가 안정적이었던 프레임 수
    "max_anxiety": 0.0,        # 면접 중 기록된 최대 긴장 수치
    "tension_events": []       # 긴장이 발생한 시점(초) 리스트
}

# 1-5. AI 모델 경로 지정
# 다운로드 받은 MediaPipe Face Landmarker 모델 파일의 위치
model_path = 'face_landmarker.task'

# ==========================================
# [Step 2] 유틸리티 함수 정의 (Helper Functions)
# ==========================================

def get_korean_font(size):
    """
    한글 폰트를 로드하는 함수입니다.
    Windows의 경우 'malgun.ttf'를 사용하고, 없으면 기본 폰트를 사용합니다.
    """
    try: 
        return ImageFont.truetype("malgun.ttf", size)
    except: 
        return ImageFont.load_default()

# 폰트 객체 미리 생성 (성능 최적화)
font_main = get_korean_font(24)  # 메인 텍스트용
font_sub = get_korean_font(18)   # 서브 정보용
font_debug = get_korean_font(14) # 디버그 정보용

def draw_korean_text(img, text, position, color, font=font_main):
    """
    OpenCV 이미지 위에 한글 텍스트를 그리는 함수입니다.
    OpenCV는 기본적으로 한글을 지원하지 않으므로 Pillow로 변환하여 그립니다.
    """
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) # CV2(BGR) -> PIL(RGB) 변환
    draw = ImageDraw.Draw(img_pil)
    draw.text(position, text, font=font, fill=color) # 텍스트 그리기
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR) # PIL(RGB) -> CV2(BGR) 재변환

# ==========================================
# [Step 3] 최종 리포트 생성 함수 (Report Generator)
# ==========================================
def generate_report():
    """
    면접 종료 시 호출되며, 누적된 session_data를 분석하여 
    터미널에 출력하고 JSON 파일로 저장합니다.
    """
    print("\n" + "="*50)
    print("🎓 AI 면접 최종 분석 리포트")
    print("="*50)
    
    total = session_data["total_frames"]
    if total == 0: return # 데이터가 없으면 종료

    # 3-1. 통계 데이터 계산 (Averages & Ratios)
    duration = time.time() - session_data["start_time"]
    avg_smile = (sum(session_data["smile_scores"]) / total) * 100
    avg_anxiety = (sum(session_data["anxiety_scores"]) / total) * 100
    gaze_ratio = (session_data["gaze_center_frames"] / total) * 100
    posture_ratio = (session_data["posture_stable_frames"] / total) * 100

    # 3-2. 평가 기준 출력
    print("📋 평가 산출 기준 (Scoring Criteria):")
    print(f"   - 자신감({WEIGHT_CONFIDENCE*100:.0f}%): 답변 중 밝은 표정(미소)을 유지한 평균 수치")
    print(f"   - 시선집중({WEIGHT_FOCUS*100:.0f}%): 영점 기준 카메라를 정면으로 응시한 시간 비율")
    print(f"   - 자세안정({WEIGHT_POSTURE*100:.0f}%): 영점 기준 바른 자세(고개 숙임/비틀림 방지) 유지 비율")
    print(f"   - 정서안정({WEIGHT_EMOTION*100:.0f}%): 미간 찌푸림 등 불안 지표가 낮게 유지된 정도")
    print("-" * 50)

    # 3-3. 가중치 적용 및 최종 점수 산출
    score_conf = avg_smile * WEIGHT_CONFIDENCE
    score_focus = gaze_ratio * WEIGHT_FOCUS
    score_posture = posture_ratio * WEIGHT_POSTURE
    score_emotion = (100 - avg_anxiety) * WEIGHT_EMOTION
    overall_score = score_conf + score_focus + score_posture + score_emotion
    
    # 3-4. 결과 출력
    print(f"⏱️ 총 면접 시간: {int(duration // 60)}분 {int(duration % 60)}초")
    print("-" * 50)
    print("🧮 상세 채점 내역 (Score Breakdown):")
    print(f"   1. 자신감: {avg_smile:5.1f}점 x {WEIGHT_CONFIDENCE:3.1f} = {score_conf:4.1f}점")
    print(f"   2. 시선집중: {gaze_ratio:5.1f}점 x {WEIGHT_FOCUS:3.1f} = {score_focus:4.1f}점")
    print(f"   3. 자세안정: {posture_ratio:5.1f}점 x {WEIGHT_POSTURE:3.1f} = {score_posture:4.1f}점")
    print(f"   4. 정서안정: {100-avg_anxiety:5.1f}점 x {WEIGHT_EMOTION:3.1f} = {score_emotion:4.1f}점")
    print(f"   -------------------------------------------")
    print(f"   ∑ 최종 합계: {score_conf:.1f} + {score_focus:.1f} + {score_posture:.1f} + {score_emotion:.1f} = {overall_score:.1f}점")
    
    print("-" * 50)
    print(f"🔥 긴장 집중 분석:")
    print(f"   - 최고 긴장 수치: {session_data['max_anxiety']*100:.1f}%")
    print(f"   - 긴장 발생 횟수: {len(session_data['tension_events'])}회")
    if session_data['tension_events']:
        intervals = ", ".join([f"{t:.1f}초" for t in session_data['tension_events'][:5]])
        print(f"   - 주요 긴장 시점: {intervals}{' ...' if len(session_data['tension_events']) > 5 else ''}")
    
    print("-" * 50)
    print(f"🏆 최종 종합 평점: {overall_score:.1f} / 100")
    print("="*50 + "\n")
    
    # 3-5. JSON 파일 저장
    report_json = {
        "score": round(overall_score, 1),
        "metrics": {"confidence": round(avg_smile, 1), "focus": round(gaze_ratio, 1), "posture": round(posture_ratio, 1), "anxiety": round(avg_anxiety, 1)},
        "tension_events": session_data['tension_events']
    }
    with open("ai-worker/cv_poc/interview_result.json", "w", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=4)
    print("💾 결과 파일이 'ai-worker/cv_poc/interview_result.json'에 저장되었습니다.\n")

# ==========================================
# [Step 4] 메인 실행 함수 (Main Loop)
# ==========================================
def run_live_vision():
    # 전역 변수 사용 선언 (영점 조절 값)
    global calibrated_gaze_x, calibrated_gaze_y, calibrated_pitch, calibrated_eye_diff, calibrated_tilt_diff
    
    session_data["start_time"] = time.time()
    
    # 4-1. MediaPipe FaceLandmarker 모델 로드 및 설정
    detector = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path), # 모델 파일 경로
        output_face_blendshapes=True, # 표정 분석을 위한 Blendshapes 활성화
        running_mode=vision.RunningMode.VIDEO # 비디오 모드 (스트림 처리)
    ))
    
    # 4-2. 웹캠 연결
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('AI Interviewer Vision System', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('AI Interviewer Vision System', 1280, 720)

    # 4-3. 프레임 루프 시작
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break # 카메라 연결 실패 시 종료
        
        # 이미지 전처리 (리사이즈 및 좌우 반전)
        frame = cv2.resize(frame, (1280, 720))
        frame = cv2.flip(frame, 1) # 거울 모드
        h, w, _ = frame.shape
        
        # MediaPipe용 이미지 변환 (BGR -> RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # [핵심] AI 추론 실행 (얼굴 감지)
        result = detector.detect_for_video(mp_image, int(time.time() * 1000))

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]
            left_iris = landmarks[468] # 왼쪽 눈동자 랜드마크 ID: 468
            
            # [Step 5] 시선(Gaze) 분석
            diff_x = left_iris.x - calibrated_gaze_x # 영점 대비 X 변화량
            diff_y = left_iris.y - calibrated_gaze_y # 영점 대비 Y 변화량
            
            gaze_label = "정면 응시"
            gaze_color = (0, 255, 255) # 노란색
            if diff_x < -GAZE_TOLERANCE_X: gaze_label = "왼쪽 주시"
            elif diff_x > GAZE_TOLERANCE_X: gaze_label = "오른쪽 주시"
            elif diff_y < -GAZE_TOLERANCE_Y: gaze_label = "위쪽 주시"
            elif diff_y > GAZE_TOLERANCE_Y: gaze_label = "아래쪽 주시"
            
            # [Step 6] 자세(Posture) 분석
            eye_diff = abs(landmarks[33].z - landmarks[263].z) # 눈 깊이 차이 (몸 비틀림)
            tilt_diff = abs(landmarks[33].y - landmarks[263].y)# 눈 높이 차이 (갸우뚱)
            nose_tip = landmarks[1]; chin = landmarks[152]
            pitch_val = chin.z - nose_tip.z # 고개 끄덕임 (Pitch) 계산
            
            # 영점 대비 오차가 허용 범위 내인지 확인
            is_posture_stable = abs(eye_diff - calibrated_eye_diff) < 0.04 and abs(tilt_diff - calibrated_tilt_diff) < 0.03
            is_head_straight = abs(pitch_val - calibrated_pitch) < HEAD_SENSITIVITY
            
            alignment_label = "✅ 안정"
            align_color = (255, 255, 0)
            if not is_posture_stable: 
                alignment_label = "⚠️ [자세 불균형]"; align_color = (100, 100, 255)
            elif not is_head_straight: 
                alignment_label = "🚫 [고개 각도 이탈]"; align_color = (50, 50, 255)

            # [Step 7] 감정(Emotion) 분석
            blendshapes = {b.category_name: b.score for b in result.face_blendshapes[0]}
            smile = (blendshapes.get('mouthSmileLeft', 0) + blendshapes.get('mouthSmileRight', 0)) / 2
            brow_down = (blendshapes.get('browDownLeft', 0) + blendshapes.get('browDownRight', 0)) / 2
            
            emotion_label = "평온"
            emotion_color = (255, 255, 255)
            if brow_down > 0.35: emotion_label, emotion_color = "❌ 긴장도 높음", (255, 50, 50)
            elif smile > 0.4: emotion_label, emotion_color = "✅ 자신감 있음", (0, 255, 0)

            # [Step 8] 데이터 누적 및 이벤트 기록
            session_data["total_frames"] += 1
            session_data["smile_scores"].append(smile)
            session_data["anxiety_scores"].append(brow_down)
            
            # 긴장 최대치 갱신
            if brow_down > session_data["max_anxiety"]: session_data["max_anxiety"] = brow_down
            
            # 긴장 이벤트 발생 시점 기록 (2초 쿨다운 적용)
            current_sec = time.time() - session_data["start_time"]
            if brow_down > 0.4:
                if not session_data["tension_events"] or (current_sec - session_data["tension_events"][-1] > 2):
                    session_data["tension_events"].append(current_sec)
                    
            if gaze_label == "정면 응시": session_data["gaze_center_frames"] += 1
            if alignment_label == "✅ 안정": session_data["posture_stable_frames"] += 1

            # [Step 9] UI 렌더링 (화면 그리기)
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (450, 310), (0, 0, 0), -1) # 반투명 배경 박스
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

            frame = draw_korean_text(frame, f"👀 시선: {gaze_label}", (20, 20), gaze_color)
            frame = draw_korean_text(frame, f"👤 자세: {alignment_label}", (20, 60), align_color)
            frame = draw_korean_text(frame, f"📊 감정: {emotion_label}", (20, 100), emotion_color)
            frame = draw_korean_text(frame, f"✨ 긍정 지수: {int(smile*100)}%", (20, 150), (0, 255, 100))
            frame = draw_korean_text(frame, f"📉 긴장 지수: {int(brow_down*100)}%", (20, 190), (255, 80, 80))
            
            # 디버깅용 좌표 정보 출력
            debug_info = f"📍 눈동자 X:{left_iris.x:.3f} Y:{left_iris.y:.3f} | 📐 각도:{pitch_val:.4f}"
            frame = draw_korean_text(frame, debug_info, (20, 235), (180, 255, 255), font=font_sub)
            frame = draw_korean_text(frame, f"🎯 설정된 영점: 시선({calibrated_gaze_x:.2f},{calibrated_gaze_y:.2f}) / 각도({calibrated_pitch:.3f})", (20, 270), (150, 150, 150), font=font_debug)

        # 하단 안내 메시지
        footer = frame.copy()
        cv2.rectangle(footer, (0, h-60), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(footer, 0.6, frame, 0.4, 0, frame)
        frame = draw_korean_text(frame, "정면 응시 후 's' : 영점조절  |  'q' : 종료 및 리포트 확인", (w//2 - 280, h - 45), (255, 255, 255))

        # 최종 화면 출력
        cv2.imshow('AI Interviewer Vision System', frame)
        
        # 키보드 입력 대기 (1ms)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break # 종료 (리포트 생성으로 이동)
        elif key == ord('s') and result.face_landmarks: # 영점 조절
            calibrated_gaze_x = left_iris.x; calibrated_gaze_y = left_iris.y
            calibrated_pitch = pitch_val; calibrated_eye_diff = eye_diff; calibrated_tilt_diff = tilt_diff
            print("✅ 영점 조절 완료! 현재 자세를 기준으로 다시 잡았습니다.")

    # [Step 10] 자원 해제 및 리포트 호출
    detector.close()
    cap.release()
    cv2.destroyAllWindows()
    generate_report() # 리포트 생성 함수 호출

# 스크립트 실행 시작점
if __name__ == "__main__":
    run_live_vision()
