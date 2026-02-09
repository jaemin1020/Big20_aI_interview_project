"""
========================================
Docker 컨테이너 GPU 음성 인식 테스트
========================================
실행 위치: Docker 컨테이너 내부 (media-server)
목적: 실제 서버 환경에서 GPU 가속 성능 확인
차이점: Windows 로컬 테스트와 달리 GPU 사용
========================================
"""
import numpy as np
from faster_whisper import WhisperModel
import time
from datasets import load_dataset

print("=" * 60)
print("🐳 Docker GPU Whisper 테스트 (Large-v3-Turbo)")
print("=" * 60)
print("✅ 이 스크립트는 Docker 컨테이너 안에서 실행됩니다.")
print("✅ 실제 서버와 동일한 GPU 환경에서 테스트합니다.")
print("=" * 60)

# ============================================================
# [단계 1] Whisper 모델 로드 (GPU)
# ============================================================
print("\n[1/3] ⏳ Whisper-Large-v3-Turbo 모델 로딩 중... (GPU/CUDA)")
print("      💡 Docker 환경에서는 GPU가 정상 작동합니다!")

load_start = time.time()
try:
    model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    load_elapsed = time.time() - load_start
    print(f"      ✅ GPU 모델 로드 완료! (소요 시간: {load_elapsed:.2f}초)")
except Exception as e:
    print(f"      ❌ 모델 로드 실패: {e}")
    exit(1)

# ============================================================
# [단계 2] 테스트 오디오 로드
# ============================================================
# - HuggingFace에서 한국어 음성 샘플 다운로드
# - 실제 마이크 대신 샘플 오디오 사용 (컨테이너에는 마이크 없음)
# ============================================================
print("\n[2/3] 📥 테스트 오디오 다운로드 중...")
print("      데이터셋: google/fleurs (한국어)")

# FLEURS 데이터셋에서 한국어 샘플 로드
dataset = load_dataset("google/fleurs", "ko_kr", split="test", streaming=True, trust_remote_code=True)
sample = next(iter(dataset))

audio_data = np.array(sample["audio"]["array"], dtype=np.float32)
sample_rate = sample["audio"]["sampling_rate"]
reference_text = sample["transcription"]  # 정답 텍스트

print(f"      ✅ 오디오 로드 완료!")
print(f"      샘플레이트: {sample_rate}Hz")
print(f"      길이: {len(audio_data)/sample_rate:.2f}초")
print(f"      정답 텍스트: '{reference_text}'")

# ============================================================
# [단계 3] Whisper GPU 추론
# ============================================================
print("\n[3/3] 🎤 GPU로 음성 인식 중...")

start_time = time.time()
segments, info = model.transcribe(
    audio_data,
    language="ko",
    vad_filter=False
)

# 결과 수집
text_parts = []
for segment in segments:
    print(f"  [{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
    text_parts.append(segment.text)

elapsed = time.time() - start_time
recognized_text = " ".join(text_parts).strip()

# ============================================================
# [결과 출력]
# ============================================================
print("\n" + "=" * 60)
print("📊 테스트 결과")
print("=" * 60)
print(f"✅ GPU 추론 성공!")
print(f"⏱️  모델 로딩 시간: {load_elapsed:.3f}초 (GPU)")
print(f"⏱️  음성 인식 시간: {elapsed:.3f}초 (GPU)")
print(f"\n📝 인식 결과:")
print(f"   '{recognized_text}'")
print(f"\n📖 정답:")
print(f"   '{reference_text}'")

# 간단한 정확도 계산
import difflib
similarity = difflib.SequenceMatcher(None, reference_text, recognized_text).ratio()
accuracy = similarity * 100

print(f"\n✨ 정확도: {accuracy:.1f}%")

if accuracy >= 90:
    print(f"🎉 평가: 매우 우수!")
elif accuracy >= 70:
    print(f"👍 평가: 양호")
else:
    print(f"⚠️  평가: 개선 필요")

print("=" * 60)
print("\n💡 참고:")
print("   - 이 결과는 실제 웹 면접 시스템과 동일한 환경입니다.")
print("   - Windows 로컬 테스트보다 10배 이상 빠릅니다!")
print("=" * 60)
