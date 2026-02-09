"""
========================================
Docker 컨테이너 GPU 음성 인식 테스트 (Large-v3)
========================================
실행 위치: Docker 컨테이너 내부 (media-server)
모델: openai/whisper-large-v3 (정확도 최우선)
목적: 실제 서버 환경에서 정확도 최우선 모델의 GPU 성능 확인
========================================
"""
import numpy as np
from faster_whisper import WhisperModel
import time
from datasets import load_dataset

print("=" * 60)
print("🐳 Docker GPU Whisper 테스트 (Large-v3)")
print("=" * 60)

# [단계 1] Whisper 모델 로드 (GPU)
print("\n[1/3] ⏳ Whisper-Large-v3 모델 로딩 중... (GPU/CUDA)")
load_start = time.time()
try:
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    load_elapsed = time.time() - load_start
    print(f"      ✅ GPU 모델 로드 완료! (소요 시간: {load_elapsed:.2f}초)")
except Exception as e:
    print(f"      ❌ 모델 로드 실패: {e}")
    exit(1)

# [단계 2] 테스트 오디오 로드 (샘플 오디오 사용)
print("\n[2/3] 📥 테스트 오디오 다운로드 중...")
dataset = load_dataset("google/fleurs", "ko_kr", split="test", streaming=True, trust_remote_code=True)
sample = next(iter(dataset))
audio_data = np.array(sample["audio"]["array"], dtype=np.float32)
sample_rate = sample["audio"]["sampling_rate"]
reference_text = sample["transcription"]

print(f"      ✅ 오디오 로드 완료! (정답: {reference_text})")

# [단계 3] Whisper GPU 추론
print("\n[3/3] 🎤 GPU로 음성 인식 중...")
start_time = time.time()
segments, info = model.transcribe(audio_data, language="ko", vad_filter=False)

text_parts = []
for segment in segments:
    print(f"  [{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
    text_parts.append(segment.text)

elapsed = time.time() - start_time
recognized_text = " ".join(text_parts).strip()

print("\n" + "=" * 60)
print("📊 테스트 결과 (Large-v3)")
print("=" * 60)
print(f"⏱️  모델 로딩 시간: {load_elapsed:.3f}초 (GPU)")
print(f"⏱️  음성 인식 시간: {elapsed:.3f}초 (GPU)")
print(f"📝 인식 결과: '{recognized_text}'")
print(f"✨ 정확도: {accuracy}% (유사도 기준)")
print("=" * 60)
