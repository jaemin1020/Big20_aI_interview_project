# syntax=docker/dockerfile:1
# GPU 가속을 위한 CUDA Devel 이미지 사용 (컴파일러 nvcc 포함)
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 1. 시스템 패키지 설치
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    build-essential cmake git pkg-config libopenblas-dev \
    ffmpeg libsm6 libxext6 libgl1 curl \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.10 /usr/bin/python
WORKDIR /app

# 2. pip 기본 업그레이드
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --upgrade pip setuptools wheel

# 3. 핵심 빌드 도구 (Numpy, Cython)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install "numpy>=1.23.0,<2.0.0" "Cython"

# 4. LLM & ML 거대 패키지 (가장 안 변하는 레이어)
# llama-cpp-python: 프리빌드 Wheel 사용 (30분 빌드 방지)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# PyTorch
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install torch==2.3.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Transformers & NLP
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install transformers==4.41.2 sentence-transformers>=3.0.0

# 5. Computer Vision & Emotion (거대 패키지 2)
# DeepFace & TensorFlow (설치 시간이 매우 긺)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install deepface>=0.0.90 tf-keras>=2.16.0 opencv-python-headless>=4.10.0.84

# 6. Audio & STT (거대 패키지 3)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install faster-whisper>=1.1.0

# 7. LangSmith (개별 설치하여 추후 업데이트 속도 향상)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install langsmith

# 8. 나머지 일반 의존성 설치 (requirements.txt)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

# 9. 소스 코드 복사
COPY . .

# 실행
CMD ["celery", "-A", "main.app", "worker", "--loglevel=info"]
