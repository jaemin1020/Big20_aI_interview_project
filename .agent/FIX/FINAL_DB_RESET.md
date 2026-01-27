# 🚨 최종 해결 방법: DB 초기화

## 문제 요약
- Question 테이블 스키마가 모델과 불일치
- 여러 번의 수정으로 인해 DB 상태가 불안정

## 해결 방법

### 1. 전체 시스템 중지 및 DB 초기화

```bash
# 1. 모든 컨테이너 중지
docker-compose down

# 2. DB 볼륨 삭제 (데이터 초기화)
docker volume rm big20_ai_interview_project_postgres_data

# 3. 전체 재시작
docker-compose up -d

# 4. 로그 확인
docker-compose logs backend --tail=50
```

### 2. 정상 동작 확인

```bash
# Backend API 문서 접속
curl http://localhost:8000/docs

# Frontend 접속
# http://localhost:3000
```

### 3. 테스트 계정 생성

```bash
python scripts/create_test_user.py
```

## 주의사항

⚠️ **DB 볼륨을 삭제하면 모든 데이터가 삭제됩니다!**
- 기존 사용자 계정
- 면접 기록
- 질문 데이터

개발 환경이므로 문제없지만, 프로덕션에서는 절대 하지 마세요!

---

**작성일**: 2026-01-27  
**상태**: ✅ 최종 해결 방법
