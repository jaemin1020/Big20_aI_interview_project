"""
Windows 로컬 Whisper 마이크 테스트
목적: Whisper 모델이 한국어 음성을 제대로 인식하는지 빠르게 확인
"""
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import time

print("=" * 60)
print("🎤 Whisper-Large-v3-Turbo 로컬 마이크 테스트")
print("=" * 60)
print("\n[알림] 이 테스트는 로컬 PC(CPU) 환경에서 실행됩니다.")
print("-" * 60)

# [Step 1] Whisper 모델 로드
print("\n[1/4] ⏳ Whisper-Large-v3-Turbo 모델 로딩 중... (CPU 모드)")
load_start = time.time()
try:
    # [핵심] 초고속 가속화 모델 'large-v3-turbo' 사용
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    load_elapsed = time.time() - load_start
    print(f"      ✅ CPU 모드 로드 완료! (소요 시간: {load_elapsed:.2f}초)")
except Exception as e:
    print(f"      ❌ 모델 로드 실패: {e}")
    exit(1)

# [Step 2] 녹음 설정
SAMPLE_RATE = 16000  # Whisper는 16kHz 권장
DURATION = 60  # [수정] 1분 자기소개 테스트를 위해 60초로 변경

print(f"\n[2/4] 🎙️  사용 가능한 마이크 목록:")
print(sd.query_devices())

print(f"\n[3/4] 🔴 {DURATION}초간 녹음을 시작합니다!")
print("      지금 긴 문장으로 말씀해주세요!")
print("      예) '안녕하세요, 저는 인공지능 면접 시스템을 테스트하고 있습니다.'")
print("-" * 60)

# 카운트다운
for i in range(3, 0, -1):
    print(f"      {i}...")
    time.sleep(1)
print("      🎤 녹음 시작!")

# [Step 3] 마이크 입력 녹음
try:
    audio_data = sd.rec(
        int(DURATION * SAMPLE_RATE), 
        samplerate=SAMPLE_RATE, 
        channels=1,  # Mono
        dtype='float32'
    )
    sd.wait()  # 녹음 완료 대기
    print("      ✅ 녹음 완료!\n")
    
    # [디버깅] 녹음된 오디오를 파일로 저장
    import scipy.io.wavfile as wav
    import os
    # 현재 스크립트가 있는 폴더 경로를 가져옵니다.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "recorded_audio.wav")
    
    wav.write(output_file, SAMPLE_RATE, audio_data)
    print(f"      💾 녹음 파일 저장: {output_file}")
    print(f"         → 이 파일을 재생해서 실제로 뭐가 녹음됐는지 확인하세요!\n")
except Exception as e:
    print(f"      ❌ 녹음 실패: {e}")
    print("\n가능한 원인:")
    print("  - 마이크 권한이 없음")
    print("  - 마이크가 연결되지 않음")
    exit(1)

# [Step 4] Whisper로 음성 인식
print("[4/4] 🔍 Whisper가 음성을 분석하는 중...")
audio_array = audio_data.flatten()  # (N, 1) -> (N,) 변환

# [디버깅] 오디오 레벨 확인
audio_max = np.abs(audio_array).max()
audio_mean = np.abs(audio_array).mean()
print(f"      📊 오디오 레벨 체크:")
print(f"         최대 볼륨: {audio_max:.4f}")
print(f"         평균 볼륨: {audio_mean:.4f}")

if audio_max < 0.01:
    print(f"      ⚠️  경고: 오디오 레벨이 매우 낮습니다! 마이크 볼륨을 높이세요.")

start_time = time.time()
segments, info = model.transcribe(
    audio_array, 
    language="ko",
    vad_filter=False
)
text_parts = []
segment_count = 0

# 각 세그먼트 출력
for segment in segments:
    segment_count += 1
    print(f"  [{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
    text_parts.append(segment.text)

elapsed = time.time() - start_time
full_text = " ".join(text_parts).strip()

print("=" * 60)
if full_text:
    print("✅ 최종 인식 텍스트:")
    print(f"   '{full_text}'")
    print(f"\n⏱️  모델 로딩 시간: {load_elapsed:.2f}초")
    print(f"⏱️  음성 인식 시간: {elapsed:.2f}초")
    print(f"📊 세그먼트 수: {segment_count}개")
    
    # [추가] 정확도 측정 (선택사항)
    print("\n" + "=" * 60)
    print("📈 정확도 측정 (선택)")
    print("=" * 60)
    ground_truth = input("실제로 말한 내용을 입력하세요 (Enter는 건너뛰기): ").strip()
    
    if ground_truth:
        # 문자 단위 정확도 (Character Accuracy)
        def calculate_char_accuracy(reference, hypothesis):
            ref = reference.replace(" ", "").lower()
            hyp = hypothesis.replace(" ", "").lower()
            
            if len(ref) == 0:
                return 0.0
            
            # Levenshtein distance (간단 구현)
            import difflib
            similarity = difflib.SequenceMatcher(None, ref, hyp).ratio()
            return similarity * 100
        
        # 단어 단위 정확도 (Word Accuracy)
        def calculate_word_accuracy(reference, hypothesis):
            ref_words = reference.split()
            hyp_words = hypothesis.split()
            
            if len(ref_words) == 0:
                return 0.0
            
            import difflib
            similarity = difflib.SequenceMatcher(None, ref_words, hyp_words).ratio()
            return similarity * 100
        
        char_acc = calculate_char_accuracy(ground_truth, full_text)
        word_acc = calculate_word_accuracy(ground_truth, full_text)
        
        print(f"\n📊 정답 문장: '{ground_truth}'")
        print(f"🤖 인식 문장: '{full_text}'")
        print(f"\n✨ 문자 정확도: {char_acc:.1f}%")
        print(f"✨ 단어 정확도: {word_acc:.1f}%")
        
        if char_acc >= 90:
            print(f"🎉 평가: 매우 우수! (90% 이상)")
        elif char_acc >= 70:
            print(f"👍 평가: 양호 (70% 이상)")
        elif char_acc >= 50:
            print(f"⚠️  평가: 보통 (50% 이상)")
        else:
            print(f"❌ 평가: 개선 필요 (50% 미만)")
else:
    print("⚠️  인식된 음성이 없습니다.")
    print("\n가능한 원인:")
    print("  1. 마이크 소리가 너무 작음")
    print("  2. 무음이었음")
    print("  3. VAD(음성 감지) 필터에 걸림")
    print("\n해결책:")
    print("  - vad_filter=False로 변경하거나")
    print("  - 마이크에 더 가까이서 크게 말해보세요")
print("=" * 60)
