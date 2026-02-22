# 개발 환경 구축 가이드 (Development Environment Setup Guide)

## 문서 정보
- **프로젝트명**: Big20 AI Interview Project
- **작성일**: 2026-01-26
- **버전**: 1.0
- **목적**: 개발 환경 구축 및 팀 협업 환경 통일

---

## 목차
1. [Python 개발 가상환경 구축](#1-python-개발-가상환경-구축)
2. [Docker 기반 컨테이너 환경 구축](#2-docker-기반-컨테이너-환경-구축)
3. [Git 저장소 생성 및 관리](#3-git-저장소-생성-및-관리)
4. [프로젝트 폴더 구조](#4-프로젝트-폴더-구조)
5. [개발 환경 통일](#5-개발-환경-통일)
6. [의존성 관리](#6-의존성-관리)
7. [환경 변수 설정](#7-환경-변수-설정)
8. [데이터베이스 초기화](#8-데이터베이스-초기화)
9. [코드 품질 관리](#9-코드-품질-관리)
10. [문서화 및 협업 도구](#10-문서화-및-협업-도구)

---

## 1. Python 개발 가상환경 구축

### 1.1 Python 버전 요구사항
- **Python 버전**: 3.10 이상 (권장: 3.10.x)
- **이유**: 
  - FastAPI, SQLModel 등 최신 라이브러리 호환성
  - Type Hints 및 Pattern Matching 지원
  - 성능 개선 (3.10 이상)

### 1.2 가상환경 생성 방법

#### 방법 1: venv (표준 라이브러리)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 방법 2: conda (Anaconda/Miniconda)
```bash
# 가상환경 생성
conda create -n big20_interview python=3.10

# 가상환경 활성화
conda activate big20_interview
```

#### 방법 3: poetry (권장 - 의존성 관리 통합)
```bash
# Poetry 설치
pip install poetry

# 프로젝트 초기화
poetry init

# 가상환경 생성 및 의존성 설치
poetry install

# 가상환경 활성화
poetry shell
```

### 1.3 가상환경 검증
```bash
# Python 버전 확인
python --version
# 출력 예시: Python 3.10.11

# pip 버전 확인
pip --version

# 가상환경 경로 확인
which python  # Linux/Mac
where python  # Windows
```

---

## 2. Docker 기반 컨테이너 환경 구축

### 2.1 Docker 환경 요구사항

#### 필수 소프트웨어
- **Docker Desktop**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **NVIDIA Docker** (GPU 사용 시): nvidia-docker2

#### 시스템 요구사항
- **OS**: Windows 10/11 Pro, Ubuntu 20.04+, macOS 12+
- **RAM**: 16GB 이상 (권장: 32GB)
- **GPU**: NVIDIA GTX 1660 Super 이상 (VRAM 6GB+)
- **CUDA**: 12.1.1
- **cuDNN**: 8.x

### 2.2 Docker 설치

#### Windows
```powershell
# Docker Desktop 설치
# https://www.docker.com/products/docker-desktop

# WSL2 활성화 (필수)
wsl --install
wsl --set-default-version 2

# NVIDIA Container Toolkit 설치 (GPU 사용 시)
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

#### Linux (Ubuntu)
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# NVIDIA Docker 설치 (GPU 사용 시)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2.3 Dockerfile 구성

#### Backend-Core (GPU 지원)
```dockerfile
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Python 3.10 설치
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# pip 업그레이드
RUN pip3 install --upgrade pip

# llama-cpp-python GPU 빌드
ENV CMAKE_ARGS="-DLLAMA_CUDA=on"
ENV FORCE_CMAKE=1
RUN pip3 install llama-cpp-python --no-cache-dir

# 의존성 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### AI-Worker (CPU 최적화)
```dockerfile
FROM python:3.10-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# pip 업그레이드
RUN pip install --upgrade pip setuptools wheel

# llama-cpp-python CPU 빌드
RUN CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
    pip install --no-cache-dir llama-cpp-python==0.2.56

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["celery", "-A", "main.app", "worker", "--loglevel=info"]
```

### 2.4 Docker Compose 구성

```yaml
services:
  db:
    image: pgvector/pgvector:pg18
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend-core
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      - db
      - redis

  ai-worker:
    build: ./ai-worker
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 32G
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
```

### 2.5 Docker 실행 및 검증

```bash
# 이미지 빌드
docker-compose build

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# GPU 사용 확인
docker exec -it interview_backend nvidia-smi

# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 중지
docker-compose down
```

---

## 3. Git 저장소 생성 및 관리

### 3.1 GitHub Repository 생성

#### 3.1.1 Repository 생성
```bash
# GitHub에서 새 Repository 생성
# Repository Name: Big20_aI_interview_project
# Description: AI-powered mock interview platform
# Visibility: Private (권장)
# Initialize: README.md, .gitignore (Python), LICENSE (MIT)
```

#### 3.1.2 로컬 저장소 초기화
```bash
# 프로젝트 폴더로 이동
cd c:\big20\Big20_aI_interview_project

# Git 초기화 (이미 되어있다면 생략)
git init

# 원격 저장소 연결
git remote add origin https://github.com/YOUR_USERNAME/Big20_aI_interview_project.git

# 기본 브랜치 설정
git branch -M main

# 초기 커밋
git add .
git commit -m "Initial commit: Project setup"
git push -u origin main
```

### 3.2 브랜치 전략 (Git Flow)

#### 3.2.1 브랜치 구조
```
main (production)
  └── develop (integration)
       ├── feature/user-auth (개인 작업)
       ├── feature/question-generation (개인 작업)
       ├── feature/emotion-analysis (개인 작업)
       └── hotfix/critical-bug (긴급 수정)
```

#### 3.2.2 브랜치 생성 및 관리
```bash
# develop 브랜치 생성
git checkout -b develop

# 개인 작업 브랜치 생성 (feature)
git checkout -b feature/your-name-task-name

# 예시
git checkout -b feature/jaemin-question-generation

# 작업 후 커밋
git add .
git commit -m "feat: Add question generation module"

# develop 브랜치로 병합
git checkout develop
git merge feature/jaemin-question-generation

# 원격 저장소에 푸시
git push origin develop
```

#### 3.2.3 커밋 메시지 규칙 (Conventional Commits)
```bash
# 형식: <type>(<scope>): <subject>

# 예시
git commit -m "feat(backend): Add JWT authentication"
git commit -m "fix(ai-worker): Fix emotion analysis error"
git commit -m "docs(readme): Update installation guide"
git commit -m "refactor(database): Optimize query performance"
git commit -m "test(api): Add unit tests for interview endpoints"
```

**Type 종류**:
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 코드 추가/수정
- `chore`: 빌드 설정, 패키지 매니저 설정 등

### 3.3 .gitignore 설정

**현재 프로젝트의 .gitignore**:
```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/

# 가상환경
.env
.venv
venv/
ENV/

# IDE
.vscode/
.idea/

# 로그
*.log

# 데이터베이스
db.sqlite3
*.db

# 모델 파일 (용량 큰 파일)
model/
models/
*.gguf
*.bin

# 환경 변수
.env
.env.local

# Docker
.dockerignore

# OS
.DS_Store
Thumbs.db

# 프로젝트 특화
Garbage/
*.tmp
```

### 3.4 Git LFS (Large File Storage) 설정

**대용량 모델 파일 관리**:
```bash
# Git LFS 설치
git lfs install

# 추적할 파일 패턴 설정
git lfs track "*.gguf"
git lfs track "*.bin"
git lfs track "*.pth"

# .gitattributes 커밋
git add .gitattributes
git commit -m "chore: Add Git LFS tracking for model files"
```

---

## 4. 프로젝트 폴더 구조

### 4.1 표준 폴더 구조

```
Big20_aI_interview_project/
├── .agent/                      # AI Agent 관련 파일
│   ├── workflows/               # 워크플로우 정의
│   └── *.md                     # 품질 체크, 리포트 등
│
├── backend-core/                # FastAPI 백엔드
│   ├── chains/                  # LLM 체인
│   ├── logs/                    # 로그 파일
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── auth.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── ai-worker/                   # Celery 워커
│   ├── tasks/                   # Celery 태스크
│   │   ├── evaluator.py
│   │   └── vision.py
│   ├── models/                  # LLM 모델 파일 (.gguf)
│   ├── logs/
│   ├── main.py
│   ├── db.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── media-server/                # WebRTC 서버
│   ├── logs/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                    # React 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   ├── api/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── Dockerfile
│   └── package.json
│
├── infra/                       # 인프라 설정
│   └── postgres/
│       └── init.sql
│
├── docu/                        # 📁 프로젝트 문서 (추가)
│   ├── architecture/            # 아키텍처 설계서
│   ├── api/                     # API 문서
│   ├── deployment/              # 배포 가이드
│   └── user-guide/              # 사용자 가이드
│
├── Final/                       # 📁 최종 산출물 (추가)
│   ├── reports/                 # 최종 보고서
│   ├── presentations/           # 발표 자료
│   └── deliverables/            # 제출 파일
│
├── Garbage/                     # 📁 이전 버전 보관 (추가)
│   ├── v0.1/
│   ├── v0.2/
│   └── deprecated/
│
├── tests/                       # 📁 테스트 코드 (추가)
│   ├── unit/                    # 단위 테스트
│   ├── integration/             # 통합 테스트
│   └── e2e/                     # E2E 테스트
│
├── scripts/                     # 📁 유틸리티 스크립트 (추가)
│   ├── setup.sh                 # 환경 설정 스크립트
│   ├── backup.sh                # 백업 스크립트
│   └── deploy.sh                # 배포 스크립트
│
├── .env                         # 환경 변수 (Git 제외)
├── .env.example                 # 환경 변수 템플릿 (Git 포함)
├── .gitignore
├── docker-compose.yml
├── README.md
└── LICENSE
```

### 4.2 폴더 생성 스크립트

#### Windows (PowerShell)
```powershell
# 프로젝트 루트에서 실행
New-Item -ItemType Directory -Force -Path "docu/architecture"
New-Item -ItemType Directory -Force -Path "docu/api"
New-Item -ItemType Directory -Force -Path "docu/deployment"
New-Item -ItemType Directory -Force -Path "docu/user-guide"
New-Item -ItemType Directory -Force -Path "Final/reports"
New-Item -ItemType Directory -Force -Path "Final/presentations"
New-Item -ItemType Directory -Force -Path "Final/deliverables"
New-Item -ItemType Directory -Force -Path "Garbage/v0.1"
New-Item -ItemType Directory -Force -Path "Garbage/deprecated"
New-Item -ItemType Directory -Force -Path "tests/unit"
New-Item -ItemType Directory -Force -Path "tests/integration"
New-Item -ItemType Directory -Force -Path "tests/e2e"
New-Item -ItemType Directory -Force -Path "scripts"
```

#### Linux/Mac (Bash)
```bash
# 프로젝트 루트에서 실행
mkdir -p docu/{architecture,api,deployment,user-guide}
mkdir -p Final/{reports,presentations,deliverables}
mkdir -p Garbage/{v0.1,deprecated}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts
```

### 4.3 폴더별 용도

| 폴더 | 용도 | Git 추적 |
|------|------|----------|
| `docu/` | 프로젝트 문서 (설계서, API 문서 등) | ✅ Yes |
| `Final/` | 최종 제출 산출물 | ✅ Yes |
| `Garbage/` | 이전 버전 백업 (로컬 보관용) | ❌ No |
| `tests/` | 테스트 코드 | ✅ Yes |
| `scripts/` | 자동화 스크립트 | ✅ Yes |
| `logs/` | 로그 파일 | ❌ No |
| `models/` | LLM 모델 파일 | ❌ No (Git LFS) |

---

## 5. 개발 환경 통일

### 5.1 Python Interpreter 통일

#### 5.1.1 VSCode Python Interpreter 설정
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",  // Windows
  // "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",  // Linux/Mac
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### 5.1.2 팀 전체 Python 버전 확인
```bash
# 프로젝트 루트에 .python-version 파일 생성
echo "3.10.11" > .python-version

# pyenv 사용 시 자동으로 해당 버전 활성화
pyenv install 3.10.11
pyenv local 3.10.11
```

### 5.2 VSCode 확장팩 통일

#### 5.2.1 필수 확장팩 목록
```json
// .vscode/extensions.json
{
  "recommendations": [
    // Python 개발
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.isort",
    
    // Docker
    "ms-azuretools.vscode-docker",
    
    // Git
    "eamodio.gitlens",
    "mhutchie.git-graph",
    
    // 코드 품질
    "streetsidesoftware.code-spell-checker",
    "editorconfig.editorconfig",
    
    // 마크다운
    "yzhang.markdown-all-in-one",
    "davidanson.vscode-markdownlint",
    
    // 유틸리티
    "gruntfuggly.todo-tree",
    "wayou.vscode-todo-highlight",
    "aaron-bond.better-comments",
    
    // AI 지원
    "github.copilot",
    "github.copilot-chat",
    
    // 프론트엔드 (React)
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "dsznajder.es7-react-js-snippets"
  ]
}
```

#### 5.2.2 확장팩 일괄 설치
```bash
# VSCode에서 권장 확장팩 설치
# Ctrl+Shift+P → "Extensions: Show Recommended Extensions" → "Install All"
```

### 5.3 EditorConfig 설정

```ini
# .editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{js,jsx,ts,tsx,json}]
indent_style = space
indent_size = 2

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

### 5.4 코드 포맷터 설정

#### Black (Python)
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
)/
'''
```

#### Prettier (JavaScript/React)
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

---

## 6. 의존성 관리

### 6.1 requirements.txt 관리

#### 6.1.1 의존성 파일 구조
```
backend-core/requirements.txt
ai-worker/requirements.txt
media-server/requirements.txt
frontend/package.json
```

#### 6.1.2 의존성 고정 (Pinning)
```txt
# ❌ 나쁜 예 (버전 미지정)
fastapi
sqlmodel

# ✅ 좋은 예 (버전 범위 지정)
fastapi>=0.109.0,<0.110.0
sqlmodel>=0.0.14,<0.1.0

# ✅ 더 좋은 예 (정확한 버전)
fastapi==0.109.2
sqlmodel==0.0.14
```

#### 6.1.3 의존성 업데이트
```bash
# 현재 설치된 패키지 목록 저장
pip freeze > requirements-freeze.txt

# 의존성 업데이트 확인
pip list --outdated

# 특정 패키지 업데이트
pip install --upgrade fastapi

# 전체 의존성 재설치
pip install -r requirements.txt --upgrade
```

### 6.2 Poetry를 통한 의존성 관리 (권장)

#### 6.2.1 Poetry 초기화
```bash
# Poetry 설치
pip install poetry

# 프로젝트 초기화
poetry init

# 의존성 추가
poetry add fastapi sqlmodel celery

# 개발 의존성 추가
poetry add --group dev pytest black flake8

# 의존성 설치
poetry install

# 의존성 업데이트
poetry update
```

#### 6.2.2 pyproject.toml 예시
```toml
[tool.poetry]
name = "big20-ai-interview"
version = "2.0.0"
description = "AI-powered mock interview platform"
authors = ["Your Team <team@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.109.0"
sqlmodel = "^0.0.14"
celery = {extras = ["redis"], version = "^5.3.6"}
langchain = "^0.1.0"
transformers = "^4.39.0"
torch = "^2.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.0.0"
flake8 = "^6.0.0"
mypy = "^1.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 6.3 Docker 이미지 레이어 캐싱 최적화

```dockerfile
# ❌ 나쁜 예 (매번 전체 재빌드)
COPY . .
RUN pip install -r requirements.txt

# ✅ 좋은 예 (requirements.txt 변경 시만 재빌드)
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

---

## 7. 환경 변수 설정

### 7.1 .env 파일 구조

#### 7.1.1 .env.example (Git 포함)
```bash
# Database
POSTGRES_USER=interview_user
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_DB=interview_db
DATABASE_URL=postgresql://interview_user:CHANGE_ME@db:5432/interview_db

# Redis
REDIS_URL=redis://redis:6379/0

# API Keys
HUGGINGFACE_API_KEY=hf_XXXXX
HUGGINGFACE_HUB_TOKEN=hf_XXXXX
DEEPGRAM_API_KEY=XXXXX

# Security
SECRET_KEY=CHANGE_ME_TO_RANDOM_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Model Paths
MODEL_PATH=/app/models/solar-10.7b-instruct-v1.0.Q8_0.gguf
N_GPU_LAYERS=0

# Logging
LOG_LEVEL=INFO
```

#### 7.1.2 .env (실제 사용, Git 제외)
```bash
# .env.example을 복사하여 실제 값 입력
cp .env.example .env

# 민감 정보 입력
POSTGRES_PASSWORD=your_secure_password_here
SECRET_KEY=your_secret_key_here
HUGGINGFACE_API_KEY=hf_your_actual_key
DEEPGRAM_API_KEY=your_deepgram_key
```

### 7.2 환경 변수 로딩

#### Python (python-dotenv)
```python
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 사용
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
```

#### Docker Compose
```yaml
services:
  backend:
    build: ./backend-core
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
```

### 7.3 환경별 설정 분리

```
.env.development   # 개발 환경
.env.staging       # 스테이징 환경
.env.production    # 프로덕션 환경
```

```bash
# 환경별 실행
docker-compose --env-file .env.development up
docker-compose --env-file .env.production up
```

---

## 8. 데이터베이스 초기화

### 8.1 PostgreSQL 초기화 스크립트

```sql
-- infra/postgres/init.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기본 사용자 생성 (선택적)
-- CREATE USER interview_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE interview_db TO interview_user;

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_interview_id ON transcripts(interview_id);
```

### 8.2 SQLModel 마이그레이션

```python
# backend-core/database.py
from sqlmodel import SQLModel, create_engine

def init_db():
    """데이터베이스 테이블 생성"""
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully")
```

### 8.3 Alembic 마이그레이션 (권장)

```bash
# Alembic 설치
pip install alembic

# 초기화
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

---

## 9. 코드 품질 관리

### 9.1 Linting (코드 스타일 검사)

#### Flake8 설정
```ini
# .flake8
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,.venv,build,dist
ignore = E203, W503
```

#### 실행
```bash
# 전체 코드 검사
flake8 .

# 특정 폴더 검사
flake8 backend-core/
```

### 9.2 Type Checking (타입 검사)

#### mypy 설정
```ini
# mypy.ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

#### 실행
```bash
# 타입 검사
mypy backend-core/
```

### 9.3 테스트

#### pytest 설정
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### 테스트 실행
```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=backend-core --cov-report=html

# 특정 테스트
pytest tests/unit/test_auth.py
```

### 9.4 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

```bash
# Pre-commit 설치
pip install pre-commit
pre-commit install

# 수동 실행
pre-commit run --all-files
```

---

## 10. 문서화 및 협업 도구

### 10.1 API 문서 자동 생성 (FastAPI)

```python
# backend-core/main.py
from fastapi import FastAPI

app = FastAPI(
    title="AI Interview API",
    description="AI-powered mock interview platform API",
    version="2.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)
```

**접속**: `http://localhost:8000/docs`

### 10.2 코드 문서화 (Docstring)

```python
def generate_questions(position: str, count: int = 5) -> List[str]:
    """
    직무 기반 면접 질문 생성
    
    Args:
        position (str): 지원 직무 (예: "백엔드 개발자")
        count (int): 생성할 질문 개수 (기본값: 5)
    
    Returns:
        List[str]: 생성된 질문 리스트
    
    Raises:
        ValueError: position이 빈 문자열인 경우
        
    Examples:
        >>> generate_questions("백엔드 개발자", 3)
        ["Python의 GIL에 대해 설명하세요", ...]
    """
    pass
```

### 10.3 README.md 작성 가이드

```markdown
# 프로젝트명

## 개요
프로젝트 설명

## 주요 기능
- 기능 1
- 기능 2

## 기술 스택
- Backend: FastAPI, PostgreSQL
- AI: LangChain, Llama-3.1-8B

## 설치 및 실행
\`\`\`bash
docker-compose up -d
\`\`\`

## API 문서
http://localhost:8000/docs

## 라이선스
MIT
```

### 10.4 협업 도구

| 도구 | 용도 | 링크 |
|------|------|------|
| **GitHub Issues** | 버그 추적, 기능 요청 | Repository → Issues |
| **GitHub Projects** | 칸반 보드, 스프린트 관리 | Repository → Projects |
| **GitHub Wiki** | 프로젝트 위키 | Repository → Wiki |
| **Slack/Discord** | 팀 커뮤니케이션 | - |
| **Notion** | 문서 관리, 회의록 | - |

---

## 부록

### A. 체크리스트

#### 초기 환경 구축
- [ ] Python 3.10 설치 확인
- [ ] 가상환경 생성 및 활성화
- [ ] Docker Desktop 설치
- [ ] NVIDIA Docker 설치 (GPU 사용 시)
- [ ] Git 설치 및 설정
- [ ] GitHub Repository 생성
- [ ] VSCode 설치 및 확장팩 설치

#### 프로젝트 설정
- [ ] .env 파일 생성 및 설정
- [ ] .gitignore 설정
- [ ] requirements.txt 확인
- [ ] Docker Compose 빌드 성공
- [ ] 데이터베이스 초기화 확인
- [ ] API 서버 실행 확인 (http://localhost:8000/docs)

#### 코드 품질
- [ ] Black 포맷터 설정
- [ ] Flake8 Linter 설정
- [ ] Pre-commit hooks 설정
- [ ] 테스트 코드 작성
- [ ] API 문서 작성

### B. 트러블슈팅

#### Docker GPU 인식 안 됨
```bash
# NVIDIA Docker 재설치
sudo apt-get purge nvidia-docker2
sudo apt-get install nvidia-docker2
sudo systemctl restart docker

# GPU 확인
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

#### Poetry 의존성 충돌
```bash
# 캐시 삭제
poetry cache clear pypi --all

# 의존성 재설치
poetry install --no-cache
```

#### PostgreSQL 연결 실패
```bash
# 컨테이너 로그 확인
docker-compose logs db

# 포트 확인
netstat -ano | findstr :5432  # Windows
lsof -i :5432  # Linux/Mac
```

---

**문서 작성자**: 엄재민  
**최종 수정일**: 2026-01-26  
**문서 버전**: 1.0
