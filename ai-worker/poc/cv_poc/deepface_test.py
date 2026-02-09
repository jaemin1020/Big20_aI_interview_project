import os
import time
from deepface import DeepFace
import json

def run_vision_test(image_path):
    print("=" * 60)
    print("🤖 AI 면접관 Visual Analysis 테스트 (DeepFace)")
    print("=" * 60)

    if not os.path.exists(image_path):
        print(f"❌ 에러: {image_path} 파일이 없습니다.")
        return

    print(f"\n[1/2] 🔍 사진 분석 중... ({image_path})")
    start_time = time.time()

    try:
        # DeepFace 분석 실행 (얼굴 인식, 나이, 성별, 감정)
        # 🧐 핵심 포인트: actions에 'emotion'을 넣어 표정을 읽습니다.
        results = DeepFace.analyze(
            img_path=image_path, 
            actions=['emotion', 'age', 'gender'],
            enforce_detection=True,  # 얼굴이 안 보이면 에러내도록 설정
            detector_backend='opencv' # 가장 가볍고 표준적인 백엔드
        )

        elapsed = time.time() - start_time
        print(f"      ✅ 분석 완료! (소요 시간: {elapsed:.2f}초)")

        # 결과 출력 (첫 번째 얼굴 기준)
        result = results[0]
        
        print("\n" + "=" * 60)
        print("📊 분석 리포트")
        print("=" * 60)
        
        # 1. 감정(표정) 분석 결과
        dominant_emotion = result['dominant_emotion']
        emotions = result['emotion']
        
        print(f"✨ 주된 표정: {dominant_emotion.upper()}")
        print("-" * 30)
        print("🌈 상세 감정 수치:")
        # 감정 수치를 보기 좋게 정렬해서 출력
        for emo, score in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {emo:10}: {score:5.2f}%")
            
        print("-" * 30)
        # 2. 기타 정보
        print(f"👤 추정 나이: {result['age']}세")
        print(f"🚻 추정 성별: {result['dominant_gender']}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 분석 실패: {str(e)}")

if __name__ == "__main__":
    # 테스트용 이미지 경로 (컨테이너 내부 경로 기준)
    # 실제 이미지가 없다면 우선 코드만 생성합니다.
    test_img = "/app/cv_poc/test_interviewee.jpg"
    run_vision_test(test_img)
