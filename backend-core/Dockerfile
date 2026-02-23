# 1. 가벼운 Python Slim 이미지 사용 (GPU 불필요)
FROM python:3.10-slim

# 시간대 설정
ENV TZ=Asia/Seoul

# 2. 시스템 패키지 설치 (빌드용)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. pip 업그레이드
RUN pip3 install --upgrade pip

# 4. 의존성 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. 실행
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]