# 설치된 패키지 목록 (Installed Packages)

**생성일**: 2026-01-26  
**Python 버전**: 3.x  
**환경**: Big20 AI Interview Project

---

## 📦 핵심 프레임워크 & 라이브러리

### Web Framework
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **fastapi** | 0.128.0 | >=0.109.0 | ✅ 최신 |
| **starlette** | 0.50.0 | - | ✅ 정상 |
| **uvicorn** | 0.40.0 | >=0.27.0 | ✅ 최신 |
| **httptools** | 0.7.1 | - | ✅ 정상 |
| **watchfiles** | 1.1.1 | - | ✅ 정상 |

### AI/ML 프레임워크
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **torch** | 2.9.1 | >=2.2.0 | ✅ 최신 |
| **transformers** | 4.57.6 | >=4.39.0 | ✅ 최신 |
| **sentence-transformers** | 5.2.0 | - | ✅ 정상 |
| **huggingface-hub** | 0.36.0 | - | ✅ 정상 |
| **safetensors** | 0.7.0 | - | ✅ 정상 |
| **tokenizers** | 0.20.3 | - | ✅ 정상 |
| **tiktoken** | 0.12.0 | - | ✅ 정상 |

### LangChain 생태계
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **langchain** | 1.2.6 | >=0.1.0 | ✅ 최신 |
| **langchain-core** | 1.2.7 | - | ✅ 정상 |
| **langchain-community** | 0.4.1 | >=0.0.1 | ✅ 최신 |
| **langchain-openai** | 1.1.7 | - | ✅ 정상 |
| **langchain-ollama** | 1.0.1 | - | ✅ 정상 |
| **langchain-chroma** | 1.1.0 | - | ✅ 정상 |
| **langchain-text-splitters** | 1.1.0 | - | ✅ 정상 |
| **langchain-classic** | 1.0.1 | - | ✅ 정상 |
| **langgraph** | 1.0.6 | - | ✅ 정상 |
| **langgraph-checkpoint** | 4.0.0 | - | ✅ 정상 |
| **langgraph-prebuilt** | 1.0.6 | - | ✅ 정상 |
| **langgraph-sdk** | 0.3.3 | - | ✅ 정상 |
| **langsmith** | 0.6.4 | - | ✅ 정상 |

### 데이터베이스 & ORM
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **SQLAlchemy** | 2.0.45 | - | ✅ 정상 |
| ⚠️ **sqlmodel** | - | >=0.0.14 | ❌ 미설치 |
| ⚠️ **psycopg2-binary** | - | >=2.9.9 | ❌ 미설치 |

### 벡터 데이터베이스
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **chromadb** | 1.4.1 | - | ✅ 정상 |
| **chroma-hnswlib** | 0.7.6 | - | ✅ 정상 |

### 보안 & 인증
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **bcrypt** | 5.0.0 | >=4.0.1 | ✅ 최신 |
| ⚠️ **python-jose** | - | >=3.3.0 | ❌ 미설치 |
| ⚠️ **passlib** | - | >=1.7.4 | ❌ 미설치 |

### API 클라이언트
| 패키지 | 설치 버전 | 프로젝트 요구 | 상태 |
|--------|-----------|---------------|------|
| **openai** | 1.109.1 | - | ✅ 정상 |
| **ollama** | 0.6.1 | - | ✅ 정상 |
| **httpx** | 0.28.1 | - | ✅ 정상 |
| **httpcore** | 1.0.9 | - | ✅ 정상 |
| **aiohttp** | 3.13.3 | - | ✅ 정상 |
| **requests** | 2.32.5 | - | ✅ 정상 |

---

## 🔧 유틸리티 & 도구

### 데이터 처리
| 패키지 | 설치 버전 |
|--------|-----------|
| **pandas** | 2.3.3 |
| **numpy** | 1.26.4 |
| **pyarrow** | 22.0.0 |
| **scikit-learn** | 1.7.2 |
| **scipy** | 1.15.3 |

### 환경 설정
| 패키지 | 설치 버전 |
|--------|-----------|
| **python-dotenv** | 1.2.1 |
| **pydantic** | 2.12.5 |
| **pydantic-core** | 2.41.5 |
| **pydantic-settings** | 2.12.0 |

### 비동기 처리
| 패키지 | 설치 버전 |
|--------|-----------|
| **anyio** | 4.12.1 |
| **asyncio** | (내장) |
| **aiosignal** | 1.4.0 |
| **async-timeout** | 4.0.3 |

### 로깅 & 모니터링
| 패키지 | 설치 버전 |
|--------|-----------|
| **coloredlogs** | 15.0.1 |
| **rich** | 14.2.0 |
| **tqdm** | 4.67.1 |

### 네트워킹
| 패키지 | 설치 버전 |
|--------|-----------|
| **websockets** | 16.0 |
| **websocket-client** | 1.9.0 |
| **urllib3** | 2.6.3 |

### OpenTelemetry (모니터링)
| 패키지 | 설치 버전 |
|--------|-----------|
| **opentelemetry-api** | 1.39.1 |
| **opentelemetry-sdk** | 1.39.1 |
| **opentelemetry-instrumentation** | 0.60b1 |
| **opentelemetry-instrumentation-fastapi** | 0.60b1 |
| **opentelemetry-exporter-otlp-proto-grpc** | 1.39.1 |

### Git & 버전 관리
| 패키지 | 설치 버전 |
|--------|-----------|
| **GitPython** | 3.1.46 |
| **gitdb** | 4.0.12 |

### Jupyter & 개발 도구
| 패키지 | 설치 버전 |
|--------|-----------|
| **ipykernel** | 7.1.0 |
| **ipython** | 8.38.0 |
| **jupyter_client** | 8.8.0 |
| **jupyter_core** | 5.9.1 |
| **ipywidgets** | 8.1.8 |

### Streamlit (대시보드)
| 패키지 | 설치 버전 |
|--------|-----------|
| **streamlit** | 1.52.2 |
| **altair** | 6.0.0 |
| **pydeck** | 0.9.1 |

---

## ⚠️ 누락된 필수 패키지

프로젝트 요구사항에는 있지만 현재 설치되지 않은 패키지:

### Backend-Core 필수 패키지
```bash
pip install sqlmodel>=0.0.14
pip install psycopg2-binary>=2.9.9
pip install python-jose[cryptography]>=3.3.0
pip install passlib[bcrypt]>=1.7.4
pip install celery[redis]>=5.3.6
pip install redis>=5.0.3
pip install python-multipart>=0.0.9
```

### AI-Worker 필수 패키지
```bash
pip install llama-cpp-python>=0.2.56
pip install deepface>=0.0.91
pip install tensorflow>=2.16.0
pip install opencv-python-headless>=4.9.0
pip install librosa>=0.10.1
```

### Media-Server 필수 패키지
```bash
pip install aiortc>=1.14.0
pip install deepgram-sdk>=5.3.1
pip install av>=14.0.0
pip install pylibsrtp>=0.10.0
```

---

## 📊 패키지 통계

- **총 설치 패키지**: 173개
- **핵심 프레임워크**: 정상 ✅
- **AI/ML 라이브러리**: 정상 ✅
- **누락된 필수 패키지**: 11개 ⚠️
- **추가 유틸리티**: 정상 ✅

---

## 🔍 주요 발견 사항

### ✅ 장점
1. **LangChain 생태계 완비** - 모든 LangChain 관련 패키지 최신 버전 설치
2. **AI/ML 프레임워크 최신** - PyTorch, Transformers 최신 버전
3. **모니터링 도구 준비** - OpenTelemetry 설치됨
4. **개발 도구 풍부** - Jupyter, Streamlit 등 설치

### ⚠️ 주의사항
1. **SQLModel 미설치** - Backend-Core의 ORM이 없음
2. **psycopg2 미설치** - PostgreSQL 연결 불가
3. **JWT 인증 라이브러리 미설치** - python-jose, passlib 없음
4. **Celery 미설치** - 비동기 작업 처리 불가
5. **WebRTC 라이브러리 미설치** - aiortc, deepgram-sdk 없음
6. **Vision 라이브러리 미설치** - DeepFace, OpenCV 없음

### 💡 권장 사항
1. 누락된 필수 패키지를 즉시 설치
2. `requirements.txt` 파일과 실제 설치 패키지 동기화
3. Docker 컨테이너 내부에서 별도로 패키지 설치 확인 필요

---

## 🚀 빠른 설치 명령어

### 모든 누락 패키지 한 번에 설치
```bash
pip install sqlmodel psycopg2-binary python-jose[cryptography] passlib[bcrypt] \
            celery[redis] redis python-multipart llama-cpp-python deepface \
            tensorflow opencv-python-headless librosa aiortc deepgram-sdk av pylibsrtp
```

### 또는 requirements.txt 사용
```bash
# Backend-Core
pip install -r backend-core/requirements.txt

# AI-Worker
pip install -r ai-worker/requirements.txt

# Media-Server
pip install -r media-server/requirements.txt
```

---

**참고**: 이 목록은 로컬 Python 환경의 패키지입니다. Docker 컨테이너 내부의 패키지는 별도로 확인이 필요합니다.

```bash
# Docker 컨테이너 내부 패키지 확인
docker exec -it interview_backend pip list
docker exec -it interview_worker pip list
docker exec -it interview_media pip list
```
