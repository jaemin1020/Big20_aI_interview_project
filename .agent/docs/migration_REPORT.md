📋 데이터베이스 구조 개선 - 마이그레이션 가이드
🎯 변경 사항 요약
1. 새로운 테이블 구조
✅ Users (기존 User 확장)
sql- id (PK)
- email (UNIQUE, INDEX)
- username (UNIQUE, INDEX)
- role (candidate/recruiter/admin)
- password_hash
- full_name
- created_at
✅ Interviews (기존 InterviewSession 개선)
sql- id (PK)
- candidate_id (FK → users.id)
- job_posting_id (FK, nullable)
- position
- status (scheduled/live/completed/cancelled)
- scheduled_time, start_time, end_time
- overall_score (평가 완료 후 업데이트)
- emotion_summary (JSONB)
🆕 Questions (질문 은행 - 신규)
sql- id (PK)
- content
- category (technical/behavioral/situational/cultural_fit)
- difficulty (easy/medium/hard)
- rubric_json (JSONB - 평가 기준)
- vector_id (pgvector 연동 준비)
- position (특정 직무 전용)
- usage_count, avg_score
- is_active
🆕 Transcripts (대화 기록 - 신규)
sql- id (PK)
- interview_id (FK → interviews.id)
- speaker (AI/User)
- text
- timestamp
- sentiment_score (-1.0 ~ 1.0)
- emotion (happy/neutral/sad/angry 등)
- question_id (FK → questions.id, nullable)
- order (대화 순서)
🆕 Evaluation_Reports (평가 리포트 - 신규)
sql- id (PK)
- interview_id (FK → interviews.id, UNIQUE)
- technical_score (0-100)
- communication_score (0-100)
- cultural_fit_score (0-100)
- summary_text
- details_json (JSONB - 상세 평가)
- evaluator_model (평가에 사용된 AI 모델)
- created_at, updated_at

🔧 마이그레이션 단계
Step 1: 기존 컨테이너 중지 및 데이터 백업
bash# 컨테이너 중지
docker-compose down

# 기존 데이터 백업 (선택)
docker exec interview_db pg_dump -U admin interview_db > backup_$(date +%Y%m%d).sql

# 볼륨 삭제 (완전 초기화)
docker volume rm $(docker volume ls -q | grep postgres)
Step 2: 파일 교체
다음 파일들을 새 버전으로 교체하세요:

backend-core/models.py → 새 DB 스키마
backend-core/main.py → 새 API 엔드포인트
ai-worker/db.py → 새 DB 헬퍼 함수
ai-worker/tasks/evaluator.py → 새 평가 로직
infra/postgres/init.sql → 새 초기화 스크립트
frontend/src/App.jsx → 새 UI 플로우
frontend/src/api/interview.js → 새 API 클라이언트

Step 3: 환경 변수 확인
.env 파일에 다음 항목이 있는지 확인:
bash# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=1234
POSTGRES_DB=interview_db
DATABASE_URL=postgresql://admin:1234@db:5432/interview_db

# Redis
REDIS_URL=redis://redis:6379/0

# API Keys
HUGGINGFACE_API_KEY=your_key_here
HUGGINGFACE_HUB_TOKEN=your_token_here
DEEPGRAM_API_KEY=your_key_here

# CORS (프로덕션 배포 시 수정)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Auth
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
Step 4: 컨테이너 재빌드 및 실행
bash# 이미지 재빌드
docker-compose build --no-cache

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
Step 5: 데이터베이스 초기화 확인
bash# PostgreSQL 접속
docker exec -it interview_db psql -U admin -d interview_db

# 테이블 확인
\dt

# 예상 출력:
#  users
#  job_postings
#  interviews
#  questions
#  transcripts
#  evaluation_reports

# 인덱스 확인
\di

# 종료
\q

🆕 주요 기능 변경사항
1. 회원가입/로그인

이메일 필드 추가: 회원가입 시 이메일 필수
역할 기반 인증: candidate/recruiter/admin 구분

2. 면접 프로세스
기존 플로우:
Session 생성 → Questions 생성 (InterviewRecord) → 답변 제출 → 평가
새 플로우:
1. Interview 생성 (status=SCHEDULED)
2. AI 질문 생성 → Questions 테이블 저장
3. Questions를 Transcripts에 AI 발화로 저장
4. 면접 시작 (status=LIVE)
5. 사용자 답변 → Transcripts에 User 발화로 저장
6. 실시간 감정 분석 → Transcripts.sentiment_score 업데이트
7. 면접 종료 (status=COMPLETED)
8. 최종 평가 리포트 생성 → Evaluation_Reports 테이블
9. Interview.overall_score 업데이트
3. 실시간 대화 기록
javascript// STT 결과를 받을 때마다 Transcript 저장
await createTranscript(
    interviewId,
    'User',  // Speaker
    sttText, // 음성 인식 텍스트
    questionId
);
4. 최종 평가 리포트
python#
ai-worker/tasks/evaluator.py
@shared_task(name="tasks.evaluator.generate_final_report")
def generate_final_report(interview_id: int):
    # 1. 전체 대화 기록 조회
    transcripts = get_interview_transcripts(interview_id)
    
    # 2. 종합 평가 (Solar LLM)
    report = eval_llm.invoke(conversation_context)
    
    # 3. DB 저장
    create_or_update_evaluation_report(
        interview_id=interview_id,
        technical_score=85.5,
        communication_score=78.2,
        cultural_fit_score=90.0,
        summary_text="전반적으로 우수한 면접 성과...",
        details_json={...}
    )

🧪 테스트 시나리오
시나리오 1: 전체 플로우 테스트
bash# 1. 회원가입
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "test1234",
    "full_name": "테스트 유저",
    "role": "candidate"
  }'

# 2. 로그인 (토큰 획득)
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test1234"
  }'

# 3. 면접 생성 (토큰 필요)
curl -X POST http://localhost:8000/interviews \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "position": "Backend Developer"
  }'

# 4. 질문 조회
curl -X GET http://localhost:8000/interviews/1/questions \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# 5. 답변 저장 (Transcript)
curl -X POST http://localhost:8000/transcripts \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_id": 1,
    "speaker": "User",
    "text": "저는 FastAPI와 PostgreSQL 경험이 3년 있습니다.",
    "question_id": 1
  }'

# 6. 면접 완료
curl -X POST http://localhost:8000/interviews/1/complete \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# 7. 평가 리포트 조회 (10초 후)
sleep 10
curl -X GET http://localhost:8000/interviews/1/report \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
시나리오 2: DB 데이터 확인
sql-- 사용자 목록
SELECT id, username, email, role FROM users;

-- 진행 중인 면접
SELECT id, candidate_id, position, status, start_time 
FROM interviews 
WHERE status = 'live';

-- 질문 은행 통계
SELECT category, difficulty, COUNT(*) as count, AVG(usage_count) as avg_usage
FROM questions
GROUP BY category, difficulty;

-- 대화 기록 (특정 면접)
SELECT speaker, text, sentiment_score, emotion, timestamp
FROM transcripts
WHERE interview_id = 1
ORDER BY timestamp;

-- 평가 리포트
SELECT 
    i.position,
    e.technical_score,
    e.communication_score,
    e.cultural_fit_score,
    e.summary_text
FROM evaluation_reports e
JOIN interviews i ON e.interview_id = i.id;

🚨 주의사항
1. 데이터 손실 방지

기존 데이터가 중요하다면 반드시 백업 후 마이그레이션하세요.
테이블 구조가 완전히 변경되어 자동 마이그레이션 불가능합니다.

2. API 엔드포인트 변경
기존신규POST /sessionsPOST /interviewsGET /sessions/{id}/questionsGET /interviews/{id}/questionsPOST /answersPOST /transcripts (Speaker="User")GET /sessions/{id}/resultsGET /interviews/{id}/report
3. 환경별 설정

개발 환경: ALLOWED_ORIGINS=* 사용 가능
프로덕션: 반드시 특정 도메인으로 제한


✅ 마이그레이션 체크리스트

 기존 데이터 백업 완료
 새 모델 파일 교체 (models.py, main.py 등)
 .env 파일 환경 변수 확인
 Docker 이미지 재빌드
 컨테이너 정상 실행 확인
 PostgreSQL 테이블 생성 확인
 API 엔드포인트 테스트
 Frontend 연동 테스트
 전체 면접 플로우 테스트
 평가 리포트 생성 확인


문제 발생 시
로그 확인
bash# Backend 로그
docker logs interview_backend --tail=100

# AI-Worker 로그
docker logs interview_worker --tail=100

# PostgreSQL 로그
docker logs interview_db --tail=50
컨테이너 재시작
bash# 전체 재시작
docker-compose restart

# 특정 서비스만
docker-compose restart backend
완전 초기화
bashdocker-compose down -v
docker-compose build --no-cache
docker-compose up -d

✨ 마이그레이션 완료 후 시스템이 정상 작동하는지 반드시 전체 플로우를 테스트하세요!