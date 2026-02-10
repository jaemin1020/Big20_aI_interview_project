# GPU 가속을 위한 CUDA Devel 이미지 사용 (컴파일러 nvcc 포함)
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 1. 시스템 패키지 및 Python 3.10 설치
# (Ubuntu 22.04 기본 파이썬은 3.10)
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# 2. pip 업그레이드
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# 3. 핵심 의존성 설치
RUN pip3 install --no-cache-dir "numpy>=1.23.0,<2.0.0" "Cython"

# 4. llama-cpp-python GPU 빌드 (cuBLAS 활성화)
# CUDA 12.1 환경에서 빌드
# -DGGML_CUDA=on : 최신 llama-cpp 옵션 (구버전은 LLAMA_CUBLAS)
RUN CMAKE_ARGS="-DGGML_CUDA=on" \
    pip3 install --no-cache-dir llama-cpp-python>=0.3.5

# 4.5 PyTorch GPU 버전 먼저 설치 (CUDA 12.1 호환)
RUN pip3 install --no-cache-dir torch==2.3.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 5. 나머지 Python 패키지 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 6. 소스 코드 복사
COPY . .

# 7. 실행 (Celery Worker)
# GPU 접근을 위해 nvidia-container-runtime 필요 (docker-compose에서 설정)
CMD ["celery", "-A", "main.app", "worker", "--loglevel=info"]
