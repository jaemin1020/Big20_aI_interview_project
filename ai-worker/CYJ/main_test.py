# CYJ/main_test.py
# AI 면접관 통합 테스트 (Isolated Test in CYJ)
# 실행 방법: docker exec -it interview_worker python /app/CYJ/main_test.py

import sys
import os
import time

# 1. 프로젝트 루트 경로 및 CYJ 모듈 경로 설정
sys.path.append("/app") # Docker 컨테이너 기준 Root
sys.path.append("/app/CYJ")

# 2. 필요한 모듈 Import
try:
    # 방금 만든 TTS 서비스
    import tts_service
    
    print("✅ 모든 모듈 Import 성공")
except ImportError as e:
    print(f"❌ 모듈 Import 실패: {e}")
    # tasks 경로가 안 잡힐 수 있으므로 경로 확인
    print(f"Current SYS.PATH: {sys.path}")
    sys.exit(1)

def main():
    print("\n" + "="*50)
    print("🧪 AI 면접관 통합 테스트 (Main Test - CYJ)")
    print("="*50)

    # [Scenario]
    # 사용자: "저는 백엔드 개발자이고 파이썬을 잘합니다."
    # AI: (생각 - 생략) -> (말하기) -> 음성 파일 생성
    
    user_position = "Python Backend Developer"
    
    # ----------------------------------------------------
    # Step 1. Think (질문 생성) - SKIPPED
    # ----------------------------------------------------
    print(f"\n[Step 1] 🧠 생각하기 (질문 생성)")
    
    # LLM 호출 생략 (사용자 요청: LLM 없는 상태 가정)
    print(f"   ℹ️ (사용자 요청에 의해 LLM 단계 건너뜀)")
    generated_text = "안녕하세요. 지금은 대규모 언어 모델 없이 음성 생성 기능만 테스트 중입니다. 목소리가 잘 들리시나요?"
    print(f"   ✅ 사용할 테스트 문장: \"{generated_text}\"")

    # ----------------------------------------------------
    # Step 2. Speak (음성 변환)
    # ----------------------------------------------------
    print(f"\n[Step 2] 🗣️ 말하기 (TTS 음성 변환)")
    
    try:
        output_file = f"/app/CYJ/outputs/test_interview_{int(time.time())}.wav"
        result_path = tts_service.generate_voice_file(generated_text, output_file)
        
        if result_path and os.path.exists(result_path):
            print(f"   ✅ 음성 파일 생성 성공!")
            print(f"   📂 저장 경로: {result_path}")
        else:
            print(f"   ❌ 음성 파일 생성 실패")
            
    except Exception as e:
        print(f"   ❌ TTS 실행 중 에러: {e}")

    print("\n" + "="*50)
    print("🎉 테스트가 완료되었습니다.")
    print("="*50)

if __name__ == "__main__":
    main()
