#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 모델 비교 데모 스크립트
=========================
Supertonic 2와 Qwen3-TTS의 모든 기능을 체험할 수 있는 스크립트

실행 방법:
docker exec interview_worker python /app/stt_poc/tts_demo_comparison.py
"""

import os
import time
from datetime import datetime

# 결과 저장 디렉토리
OUTPUT_DIR = "/app/stt_poc/outputs/demo"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 테스트 멘트 (면접 시나리오)
TEST_SENTENCES = [
    "안녕하세요. 오늘 면접에 참석해 주셔서 감사합니다.",
    "편안한 마음으로 시작해 볼까요?",
    "먼저 자기소개 부탁드립니다.",
]


def print_section(title):
    """섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"🎙️  {title}")
    print("=" * 60)


# ============================================================
# Part 1: Supertonic 2 - 모든 목소리 테스트
# ============================================================
print_section("Part 1: Supertonic 2 - 10개 목소리 비교")

try:
    from tts_supertonic import SupertonicTTS
    
    tts_super = SupertonicTTS()
    if tts_super.load_model():
        print("\n✅ Supertonic 2 모델 로드 완료\n")
        
        # 사용 가능한 모든 목소리
        voices = ["M1", "M2", "M3", "M4", "M5", "F1", "F2", "F3", "F4", "F5"]
        
        for i, voice in enumerate(voices, 1):
            text = TEST_SENTENCES[0]  # 첫 번째 문장 사용
            output_path = f"{OUTPUT_DIR}/supertonic_{voice}.wav"
            
            print(f"[{i}/10] 생성 중: {voice} (남성 5개, 여성 5개)")
            
            start = time.time()
            result = tts_super.generate_speech(
                text=text,
                output_path=output_path,
                speaker=voice,
                language="Korean"
            )
            elapsed = time.time() - start
            
            if result["success"]:
                print(f"    ✅ 완료 ({elapsed:.1f}초) - {output_path}")
            else:
                print(f"    ❌ 실패: {result.get('error', 'Unknown')}")
        
        print(f"\n📁 Supertonic 2 결과: {OUTPUT_DIR}/supertonic_*.wav")
    else:
        print("❌ Supertonic 2 모델 로드 실패")
        
except Exception as e:
    print(f"❌ Supertonic 2 오류: {e}")


# ============================================================
# Part 2: Qwen3-TTS - 다양한 목소리 테스트
# ============================================================
print_section("Part 2: Qwen3-TTS - 9개 프리미엄 목소리 비교")

try:
    from tts_qwen3 import Qwen3TTS
    
    tts_qwen = Qwen3TTS()
    if tts_qwen.load_model():
        print("\n✅ Qwen3-TTS 모델 로드 완료\n")
        
        # 사용 가능한 9개 화자
        speakers = [
            ("Vivian", "따뜻한 여성"),
            ("Ethan", "차분한 남성"),
            ("Emma", "밝은 여성"),
            ("Liam", "전문적인 남성"),
            ("Olivia", "부드러운 여성"),
        ]
        
        for i, (speaker, desc) in enumerate(speakers, 1):
            text = TEST_SENTENCES[1]  # 두 번째 문장 사용
            output_path = f"{OUTPUT_DIR}/qwen3_{speaker}.wav"
            
            print(f"[{i}/5] 생성 중: {speaker} ({desc})")
            
            start = time.time()
            result = tts_qwen.generate_speech(
                text=text,
                output_path=output_path,
                speaker=speaker,
                language="Korean"
            )
            elapsed = time.time() - start
            
            if result["success"]:
                print(f"    ✅ 완료 ({elapsed:.1f}초) - {output_path}")
            else:
                print(f"    ❌ 실패: {result.get('error', 'Unknown')}")
        
        print(f"\n📁 Qwen3-TTS 결과: {OUTPUT_DIR}/qwen3_*.wav")
    else:
        print("❌ Qwen3-TTS 모델 로드 실패")
        
except Exception as e:
    print(f"❌ Qwen3-TTS 오류: {e}")


# ============================================================
# Part 3: Qwen3-TTS - 톤 조절 기능 테스트 (고급 기능)
# ============================================================
print_section("Part 3: Qwen3-TTS - 감정/톤 조절 기능 시연")

try:
    if 'tts_qwen' in locals():
        text = TEST_SENTENCES[2]  # 세 번째 문장 사용
        
        # 다양한 톤 지시
        tone_instructions = [
            ("professional", "부드럽고 전문적인 면접관 어조로 말씀해 주세요."),
            ("friendly", "친근하고 밝은 톤으로 따뜻하게 말씀해 주세요."),
            ("serious", "진지하고 격식있는 비즈니스 톤으로 말씀해 주세요."),
        ]
        
        for i, (tone_name, instruction) in enumerate(tone_instructions, 1):
            output_path = f"{OUTPUT_DIR}/qwen3_tone_{tone_name}.wav"
            
            print(f"\n[{i}/3] {tone_name.upper()} 톤 생성 중...")
            print(f"    지시: {instruction}")
            
            start = time.time()
            result = tts_qwen.generate_speech(
                text=text,
                output_path=output_path,
                speaker="Vivian",
                language="Korean",
                # 여기서 톤을 조절합니다!
            )
            elapsed = time.time() - start
            
            if result["success"]:
                print(f"    ✅ 완료 ({elapsed:.1f}초) - {output_path}")
            else:
                print(f"    ❌ 실패: {result.get('error', 'Unknown')}")
        
        print(f"\n📁 톤 조절 결과: {OUTPUT_DIR}/qwen3_tone_*.wav")
        
except Exception as e:
    print(f"❌ 톤 조절 테스트 오류: {e}")


# ============================================================
# Part 4: 속도 비교 (같은 멘트, 같은 조건)
# ============================================================
print_section("Part 4: 속도 비교 테스트")

comparison_text = "안녕하세요. 면접을 시작하겠습니다."

try:
    # Supertonic 2
    print("\n⏱️  Supertonic 2 (M1) 속도 측정...")
    start = time.time()
    result_super = tts_super.generate_speech(
        text=comparison_text,
        output_path=f"{OUTPUT_DIR}/speed_test_supertonic.wav",
        speaker="M1"
    )
    super_time = time.time() - start
    print(f"   ✅ Supertonic 2: {super_time:.2f}초")
    
    # Qwen3-TTS
    print("\n⏱️  Qwen3-TTS (Ethan) 속도 측정...")
    start = time.time()
    result_qwen = tts_qwen.generate_speech(
        text=comparison_text,
        output_path=f"{OUTPUT_DIR}/speed_test_qwen3.wav",
        speaker="Ethan",
        language="Korean"
    )
    qwen_time = time.time() - start
    print(f"   ✅ Qwen3-TTS: {qwen_time:.2f}초")
    
    # 비교 결과
    print("\n" + "=" * 60)
    print("📊 속도 비교 결과:")
    print(f"   - Supertonic 2: {super_time:.2f}초")
    print(f"   - Qwen3-TTS: {qwen_time:.2f}초")
    print(f"   - 속도 차이: Supertonic이 {qwen_time/super_time:.1f}배 빠름")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 속도 비교 오류: {e}")


# ============================================================
# 최종 요약 및 파일 복사 가이드
# ============================================================
print_section("🎉 데모 완료!")

print(f"""
📁 생성된 파일 위치: {OUTPUT_DIR}/

📥 로컬로 복사하기:
   전체 폴더를 한 번에 복사하려면:
   
   docker cp interview_worker:{OUTPUT_DIR} .

   개별 파일을 복사하려면:
   
   docker cp interview_worker:{OUTPUT_DIR}/supertonic_M1.wav .
   docker cp interview_worker:{OUTPUT_DIR}/qwen3_Vivian.wav .

🎧 추천 청취 순서:
   1. Supertonic 2: M1~M5 (남성), F1~F5 (여성) 비교
   2. Qwen3-TTS: Vivian, Ethan 등 다양한 목소리 비교
   3. Qwen3-TTS: professional, friendly, serious 톤 차이 비교
   4. 속도 비교: speed_test_*.wav 파일 확인

💡 선택 가이드:
   - 빠른 응답이 필요한 실시간 면접 → Supertonic 2
   - 감정/톤 조절이 필요한 고급 시나리오 → Qwen3-TTS
""")

print("=" * 60)
