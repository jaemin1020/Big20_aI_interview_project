FROM python:3.10-slim

# 1. 시스템 의존성 설치 (OpenCV, Llama-cpp, DeepFace 및 빌드를 위한 도구)
# 한국 미러(KAIST) 사용으로 속도 및 안정성 향상
RUN sed -i 's/deb.debian.org/ftp.kaist.ac.kr/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --fix-missing \
    build-essential \
    cmake \
    git \
    pkg-config \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    libopenblas-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. pip 환경 최적화
# 최신 패키지 빌드 및 wheel 설치를 위해 pip, setuptools, wheel 최신화 필수
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 3. 핵심 의존성 선행 설치
# 네트워크 불안정을 방지하기 위해 timeout과 retries를 넉넉하게 설정합니다.
RUN pip install --no-cache-dir --timeout 100 --retries 10 "numpy>=1.23.0,<2.0.0" "Cython"

# 4. llama-cpp-python 설치
# 네트워크 불안정을 위해 timeout과 retries를 추가하고, CPU 최적화를 위해 OpenBLAS를 사용합니다.
RUN CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
    pip install --no-cache-dir llama-cpp-python>=0.3.5

# 5. 나머지 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --retries 5 -r requirements.txt

# 6. 소스 코드 및 모델 경로 설정
COPY . .

# JSON 로그 및 모듈 경로 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 7. Worker 실행 (Solar 모델 및 감정 분석 태스크 처리)
CMD ["celery", "-A", "main.app", "worker", "--loglevel=info"]
