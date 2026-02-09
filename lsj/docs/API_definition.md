# 산출물3 : Final_Project_API_정의서

---

## 1. 문서 개요

### 1.1 목적

본 문서는 **Big20 AI Interview Project**의 백엔드 API 엔드포인트들에 대한 상세 정의서입니다.
프론트엔드(`frontend/src/api/interview.js`)와 백엔드(`backend-core/main.py`) 코드를 기반으로 작성되었으며, 각 API의 요청/응답 구조, 인증 방식, 상태 코드, 그리고 사용 시나리오를 명확히 정의합니다.

### 1.2 기술 스택

- **Backend Framework**: FastAPI (Python)
- **Frontend HTTP Client**: Axios
- **Authentication**: OAuth2 Password Flow (JWT Bearer Token)
- **비동기 작업**: Celery + Redis (질문 생성, 답변 평가)

---

## 2. API 설계 원칙

1. **기능 단위 API 분리**: 인증, 세션 관리, 질문/답변, 평가 등 기능별로 엔드포인트 분리
2. **화면 이벤트 기반 호출**: 프론트엔드의 사용자 액션(회원가입, 로그인, 면접 시작 등)에 따라 API 호출
3. **상태(State) 중심 설계**: 세션 상태(`started`, `completed`)와 답변 상태를 관리하여 워크플로우 제어
4. **비동기 처리 우선 적용**: 질문 생성, STT 처리, LLM 평가는 Celery를 통해 비동기 처리
5. **JWT 기반 인증**: `/token` 엔드포인트에서 발급된 토큰을 `Authorization: Bearer <token>` 헤더로 전송

---

## 3. Base URL 및 인증

### 3.1 Base URL

```
http://localhost:8000
```

*Production 환경에서는 환경변수로 관리*

### 3.2 인증 방식

- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <access_token>`
- **토큰 발급**: `POST /token` 엔드포인트
- **토큰 만료 시간**: 30분 (기본값, 백엔드 설정에 따라 변경 가능)

**인증이 필요한 엔드포인트:**

- `/users/me`
- `/sessions` (POST)
- `/sessions/{session_id}/questions` (GET)
- `/answers` (POST)
- `/sessions/{session_id}/results` (GET)

---

## 4. API 엔드포인트 상세 정의

### 4.1 인증 관련 API

#### 4.1.1 회원가입

**사용자 계정을 생성합니다.**

- **Endpoint**: `POST /register`
- **인증 필요**: ❌
- **Request Body**:

```json
{
  "username": "string (required)",
  "hashed_password": "string (required)",
  "full_name": "string (optional)"
}
```

- **Response (Success 200)**:

```json
{
  "username": "john_doe",
  "id": 1
}
```

- **Error Responses**:

  - `400 Bad Request`: Username already registered

  ```json
  {
    "detail": "Username already registered"
  }
  ```

---

#### 4.1.2 로그인 (토큰 발급)

**사용자 인증 후 JWT 액세스 토큰을 발급합니다.**

- **Endpoint**: `POST /token`
- **인증 필요**: ❌
- **Request Body (Form-Data)**:

  - `username`: string
  - `password`: string
- **Response (Success 200)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

- **Error Responses**:

  - `401 Unauthorized`: Incorrect username or password

  ```json
  {
    "detail": "Incorrect username or password"
  }
  ```

**프론트엔드 처리**: 토큰을 `localStorage`에 저장하고, 이후 모든 요청에 포함

---

#### 4.1.3 현재 사용자 정보 조회

**현재 로그인한 사용자의 정보를 반환합니다.**

- **Endpoint**: `GET /users/me`
- **인증 필요**: ✅
- **Response (Success 200)**:

```json
{
  "id": 1,
  "username": "john_doe",
  "full_name": "John Doe",
  "created_at": "2026-01-23T07:00:00Z"
}
```

---

### 4.2 세션 관리 API

#### 4.2.1 면접 세션 생성

**새로운 면접 세션을 생성하고, AI가 직무에 맞는 질문을 자동으로 생성합니다.**

- **Endpoint**: `POST /sessions`
- **인증 필요**: ✅
- **Request Body**:

```json
{
  "user_name": "김철수",
  "position": "Backend Developer"
}
```

- **Response (Success 200)**:

```json
{
  "id": 42,
  "user_id": 1,
  "user_name": "김철수",
  "position": "Backend Developer",
  "status": "started",
  "emotion_summary": null,
  "created_at": "2026-01-23T08:00:00Z"
}
```

**비동기 처리**:

- Celery Task `tasks.question_generator.generate_questions`을 호출하여 질문 생성
- 생성된 질문은 `InterviewRecord` 테이블에 자동 저장 (order별로 정렬)
- 최대 30초 타임아웃 (실패 시 fallback 질문 사용)

---

### 4.3 질문/답변 API

#### 4.3.1 세션 질문 목록 조회

**특정 세션의 모든 질문을 순서대로 조회합니다.**

- **Endpoint**: `GET /sessions/{session_id}/questions`
- **인증 필요**: ✅
- **Path Parameters**:

  `session_id`: integer (면접 세션 ID)
- **Response (Success 200)**:

```json
[
  {
    "id": 101,
    "session_id": 42,
    "question_text": "Backend Developer 직무의 핵심 역량은 무엇인가요?",
    "order": 1,
    "answer_text": null,
    "evaluation": null,
    "emotion_summary": null,
    "answered_at": null,
    "created_at": "2026-01-23T08:00:05Z"
  },
  {
    "id": 102,
    "session_id": 42,
    "question_text": "RESTful API 설계 시 고려해야 할 사항을 설명해주세요.",
    "order": 2,
    "answer_text": null,
    "evaluation": null,
    "emotion_summary": null,
    "answered_at": null,
    "created_at": "2026-01-23T08:00:05Z"
  }
]
```

**사용 시나리오**: 면접 화면 진입 시 모든 질문을 미리 로드하여 순차적으로 표시

---

#### 4.3.2 답변 제출

**사용자의 답변을 서버에 제출하고, 비동기로 평가 작업을 시작합니다.**

- **Endpoint**: `POST /answers`
- **인증 필요**: ✅
- **Request Body**:

```json
{
  "record_id": 101,
  "answer_text": "RESTful API 설계 시에는 HTTP 메서드의 의미를 명확히 하고, URI는 리소스 중심으로 설계해야 합니다..."
}
```

- **Response (Success 200)**:

```json
{
  "status": "submitted",
  "record_id": 101
}
```

**비동기 처리**:

- 답변 제출 즉시 DB에 저장 (`answer_text`, `answered_at` 업데이트)
- Celery Task `tasks.evaluator.analyze_answer`를 백그라운드에서 실행
- 평가 결과는 나중에 `/sessions/{session_id}/results`에서 조회 가능

---

### 4.4 평가 및 결과 API

#### 4.4.1 세션 결과 조회

**면접 세션의 모든 질문, 답변, 평가, 감정 분석 결과를 조회합니다.**

- **Endpoint**: `GET /sessions/{session_id}/results`
- **인증 필요**: ✅
- **Path Parameters**:

  - `session_id`: integer
- **Response (Success 200)**:

```json
[
  {
    "question": "Backend Developer 직무의 핵심 역량은 무엇인가요?",
    "answer": "데이터베이스 설계, API 개발, 성능 최적화 등이 핵심 역량입니다...",
    "evaluation": {
      "score": 85,
      "feedback": "구체적인 경험을 예시로 든 점이 좋습니다.",
      "keywords": ["REST API", "Async", "Optimization"],
      "strengths": ["Clear communication"],
      "improvements": ["Need deeper technical explanation"]
    },
    "emotion": {
      "dominant_emotion": "confidence",
      "emotion_scores": {
        "confidence": 0.85,
        "nervousness": 0.10
      }
    }
  },
  {
    "question": "RESTful API 설계 시 고려사항은?",
    "answer": null,
    "evaluation": null,
    "emotion": null
  }
]
```

**사용 시나리오**:

- 면접 종료 후 결과 화면에서 호출
- 답변하지 않은 질문은 `null` 값으로 표시

---

## 5. 데이터 모델 (Request/Response Schema)

### 5.1 User Model

```typescript
interface User {
  id: number;
  username: string;
  hashed_password: string; // 회원가입 시에만 사용
  full_name?: string;
  created_at: string; // ISO 8601 format
}
```

### 5.2 InterviewSession Model

```typescript
interface InterviewSession {
  id: number;
  user_id: number;
  user_name: string;
  position: string;
  status: "started" | "completed";
  emotion_summary?: EmotionSummary;
  created_at: string;
}
```

### 5.3 InterviewRecord Model

```typescript
interface InterviewRecord {
  id: number;
  session_id: number;
  question_text: string;
  order: number;
  answer_text?: string;
  evaluation?: Evaluation;
  emotion_summary?: EmotionSummary;
  answered_at?: string;
  created_at: string;
}
```

### 5.4 Evaluation Schema (JSONB)

```typescript
interface Evaluation {
  score: number; // 0-100
  feedback: string;
  keywords: string[];
  strengths: string[];
  improvements: string[];
}
```

### 5.5 EmotionSummary Schema (JSONB)

```typescript
interface EmotionSummary {
  dominant_emotion: string;
  emotion_scores: {
    confidence: number;
    nervousness: number;
    excitement: number;
  };
  facial_expression_data?: any; // 선택적
}
```

---

## 6. 비동기 처리 API 설계

### 6.1 질문 생성 (Celery Task)

- **Task Name**: `tasks.question_generator.generate_questions`
- **호출 위치**: `POST /sessions`
- **처리 방식**:
  - Celery를 통해 AI-Worker에 요청
  - 동기 대기 (timeout: 30초)
  - 실패 시 fallback 질문 사용

### 6.2 답변 평가 (Celery Task)

- **Task Name**: `tasks.evaluator.analyze_answer`
- **호출 위치**: `POST /answers`
- **처리 방식**:
  - 비동기 전송 (응답 대기 없음)
  - 평가 완료 시 DB의 `evaluation` 필드 업데이트
  - 프론트엔드는 `/results` 엔드포인트에서 주기적으로 폴링 또는 WebSocket 사용 (향후 개선)

---

## 7. 오류 및 예외 응답 설계

### 7.1 오류 응답 구조

FastAPI의 기본 HTTPException 형식을 따릅니다.

```json
{
  "detail": "Error message description"
}
```

### 7.2 주요 상태 코드

| 상태 코드                     | 설명        | 발생 상황                                |
| :---------------------------- | :---------- | :--------------------------------------- |
| `200 OK`                    | 요청 성공   | 정상 처리                                |
| `400 Bad Request`           | 잘못된 요청 | 중복 회원가입, 필수 파라미터 누락        |
| `401 Unauthorized`          | 인증 실패   | 잘못된 토큰, 만료된 토큰                 |
| `403 Forbidden`             | 권한 없음   | 다른 사용자의 세션 접근 시도 (향후 구현) |
| `404 Not Found`             | 리소스 없음 | 존재하지 않는 session_id, record_id      |
| `500 Internal Server Error` | 서버 오류   | DB 연결 실패, 예상치 못한 예외           |

### 7.3 Retry 가능 여부

- `401 Unauthorized`: 토큰 재발급 필요 → `/token` 재호출
- `500 Internal Server Error`: 재시도 가능 (exponential backoff 권장)
- `400, 404`: 재시도 불가 (클라이언트 오류)

---

## 8. 프론트엔드 연동 가이드

### 8.1 Axios Interceptor

`frontend/src/api/interview.js`에서 모든 요청에 자동으로 토큰을 포함합니다.

```javascript
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
```

### 8.2 일반적인 워크플로우

1. **회원가입/로그인**: `POST /register` → `POST /token` → 토큰 저장
2. **면접 시작**: `POST /sessions` → 세션 ID 획득
3. **질문 로드**: `GET /sessions/{session_id}/questions` → 질문 목록 표시
4. **답변 제출**: 각 질문마다 `POST /answers` 호출
5. **결과 확인**: `GET /sessions/{session_id}/results` → 평가 결과 표시

---

## 9. 기대 효과 및 확장성

### 9.1 기대 효과

- ✅ **API 역할 명확화**: 각 엔드포인트의 책임이 명확하여 유지보수 용이
- ✅ **프론트엔드 연동 용이**: 타입스크립트 인터페이스 기반으로 타입 안정성 확보
- ✅ **비동기 처리 분리**: 시간이 오래 걸리는 작업을 백그라운드에서 처리하여 UX 개선

### 9.2 향후 확장 가능 항목

- **WebSocket 지원**: 실시간 평가 결과 푸시 (폴링 방식 개선)
- **세션 상태 전환 API**: `PATCH /sessions/{id}` (started → completed)
- **질문 추가 생성**: `POST /sessions/{id}/questions` (동적 후속 질문)
- **비디오 업로드 API**: STT 및 감정 분석을 위한 영상 파일 업로드 지원

---

## 부록. API 테스트 예시 (cURL)

### A.1 회원가입

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","hashed_password":"pass123","full_name":"Test User"}'
```

### A.2 로그인

```bash
curl -X POST http://localhost:8000/token \
  -d "username=testuser&password=pass123"
```

### A.3 세션 생성 (인증 필요)

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"user_name":"김철수","position":"Backend Developer"}'
```
