# syntax=docker/dockerfile:1
# GPU 가속을 위한 CUDA Devel 이미지 사용 (컴파일러 nvcc 포함)
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 1. 시스템 패키지 설치 (apt 캐시 마운트 적용)
# Python 3.10 및 필수 빌드 도구 설치
# /var/cache/apt 및 /var/lib/apt를 마운트하여 패키지 다운로드 캐싱
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    cmake \
    git \
    pkg-config \
    libopenblas-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# python3 -> python 심볼릭 링크
RUN ln -s /usr/bin/python3.10 /usr/bin/python

WORKDIR /app

# 2. pip 업그레이드 (pip 캐시 마운트 적용)
# --no-cache-dir 옵션을 제거하고 --mount=type=cache 사용
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --upgrade pip setuptools wheel

# 3. 핵심 의존성 설치
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install "numpy>=1.23.0,<2.0.0" "Cython"

# 4. llama-cpp-python GPU 빌드 (cuBLAS 활성화)
# CUDA stubs 경로 추가 + pip 캐시 사용
RUN --mount=type=cache,target=/root/.cache/pip \
    CMAKE_ARGS="-DGGML_CUDA=on" \
    LIBRARY_PATH=/usr/local/cuda/lib64/stubs:$LIBRARY_PATH \
    pip3 install llama-cpp-python>=0.3.5

# 4.5 PyTorch GPU 버전 먼저 설치 (CUDA 12.1 호환)
# 대용량 파일이므로 캐시 효과가 가장 큼
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install torch==2.3.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 5. 나머지 Python 패키지 설치
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

# 6. 소스 코드 복사
COPY . .

# 7. 실행 (Celery Worker)
CMD ["celery", "-A", "main.app", "worker", "--loglevel=info"]
