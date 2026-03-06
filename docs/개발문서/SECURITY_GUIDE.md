# 보안 가이드 (Security Guide)

## 🔒 보안 체크리스트

### 1. 환경 변수 관리

#### ❌ 절대 하지 말아야 할 것
- `.env` 파일을 Git에 커밋하지 마세요
- API 키를 코드에 하드코딩하지 마세요
- 프로덕션 비밀번호를 개발 환경과 동일하게 사용하지 마세요

#### ✅ 권장 사항
1. **`.env.example` 사용**
   ```bash
   cp .env.example .env
   # .env 파일을 열어 실제 값으로 교체
   ```

2. **강력한 시크릿 생성**
   ```python
   # Python으로 안전한 SECRET_KEY 생성
   import secrets
   print(secrets.token_urlsafe(32))
   ```

3. **프로덕션 환경**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - 환경 변수 (Docker Secrets, Kubernetes Secrets)

### 2. API 키 관리

#### 현재 사용 중인 API 키
- **Huggingface API Key**: LLM 모델 다운로드 및 추론
- **Deepgram API Key**: 음성-텍스트 변환 (STT)

#### 키 발급 방법
1. **Huggingface**
   - https://huggingface.co/settings/tokens
   - "New token" → Read 권한 선택

2. **Deepgram**
   - https://console.deepgram.com/
   - "Create API Key" → 프로젝트 선택

#### 키 보안
```bash
# ❌ 잘못된 예
export DEEPGRAM_API_KEY=f9ea579fb6ea6a2d98781077b1821bc3d79f6600

# ✅ 올바른 예 (.env 파일 사용)
echo "DEEPGRAM_API_KEY=your_key_here" >> .env
```

### 3. 데이터베이스 보안

#### 비밀번호 정책
```python
# backend-core/auth.py에 추가 권장
import re

def validate_password(password: str) -> bool:
    """
    비밀번호 복잡도 검증
    - 최소 8자
    - 대문자, 소문자, 숫자, 특수문자 각 1개 이상
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True
```

#### DB 접근 제어
```yaml
# docker-compose.yml
db:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # ✅ 환경 변수 사용
    # POSTGRES_PASSWORD: 1234  # ❌ 하드코딩 금지
```

### 4. CORS 설정

#### 개발 환경
```python
# backend-core/main.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
```

#### 프로덕션 환경
```bash
# .env
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 5. JWT 토큰 보안

#### 현재 설정
```python
# .env
SECRET_KEY=your_secret_key_here_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### 권장 사항
- **SECRET_KEY**: 최소 32자 이상의 무작위 문자열
- **만료 시간**: 프로덕션에서는 15-30분 권장
- **Refresh Token**: 장기 세션을 위해 구현 고려

### 6. Rate Limiting

#### 구현 예시 (FastAPI)
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/auth/login")
@limiter.limit("5/minute")  # 1분에 5번까지만 허용
async def login(request: Request, ...):
    ...
```

### 7. Input Validation

#### SQL Injection 방지
✅ **현재 상태**: SQLModel 사용으로 기본 방어됨

#### XSS 방지
```python
# 사용자 입력 검증
from html import escape

def sanitize_input(text: str) -> str:
    return escape(text)
```

### 8. HTTPS 강제 (프로덕션)

#### Nginx 설정 예시
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://backend:8000;
    }
}
```

### 9. 로깅 및 모니터링

#### 민감 정보 로깅 금지
```python
# ❌ 잘못된 예
logger.info(f"User password: {password}")

# ✅ 올바른 예
logger.info(f"User {username} logged in successfully")
```

#### 보안 이벤트 로깅
- 로그인 실패 (브루트포스 공격 감지)
- 권한 없는 접근 시도
- API 키 사용 이력

### 10. 의존성 보안

#### 정기적인 업데이트
```bash
# 취약점 스캔
pip install safety
safety check

# 의존성 업데이트
pip list --outdated
```

#### Dependabot 설정 (GitHub)
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend-core"
    schedule:
      interval: "weekly"
```

---

## 🚨 긴급 대응 절차

### API 키 유출 시
1. **즉시 키 비활성화**
   - Huggingface: https://huggingface.co/settings/tokens
   - Deepgram: https://console.deepgram.com/

2. **새 키 발급 및 교체**
   ```bash
   # .env 파일 업데이트
   vim .env
   
   # 서비스 재시작
   docker-compose restart
   ```

3. **Git 히스토리 정리** (이미 커밋된 경우)
   ```bash
   # BFG Repo-Cleaner 사용
   java -jar bfg.jar --replace-text passwords.txt .git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

### 데이터 유출 의심 시
1. 즉시 DB 접근 차단
2. 로그 분석
3. 영향 범위 파악
4. 사용자 통지 (필요 시)

---

## 📋 보안 감사 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] 모든 API 키가 환경 변수로 관리되는가?
- [ ] 비밀번호 복잡도 정책이 구현되어 있는가?
- [ ] CORS 설정이 프로덕션 환경에 맞게 되어 있는가?
- [ ] Rate Limiting이 구현되어 있는가?
- [ ] HTTPS가 강제되는가? (프로덕션)
- [ ] 민감 정보가 로그에 기록되지 않는가?
- [ ] 의존성 취약점 스캔을 정기적으로 수행하는가?
- [ ] JWT 토큰 만료 시간이 적절한가?
- [ ] 사용자 입력 검증이 충분한가?

---

**마지막 업데이트**: 2026-02-05  
**담당자**: DevOps Team
