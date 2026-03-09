# DB 초기화 및 복구 가이드

**상태**: DB 볼륨 초기화 및 컨테이너 재빌드 진행 중

현재 `docker-compose up -d --build` 명령어가 백그라운드에서 실행 중입니다.
대용량 라이브러리(NVIDIA CUDA 등) 다운로드로 인해 시간이 소요되고 있습니다.

---

## 🚀 빌드 완료 후 필수 작업

컨테이너가 모두 실행된 후(약 5~10분 소요 예상), 아래 명령어를 차례로 실행하여 DB를 초기화해주세요.

### 1. 컨테이너 상태 확인
```bash
docker ps
# 모든 컨테이너(backend, worker, media, app 등)가 "Up" 상태여야 합니다.
```

### 2. DB 마이그레이션 (테이블 생성)
```bash
# Backend 컨테이너에서 Alembic 실행
docker exec -it interview_backend alembic revision --autogenerate -m "Initial migration after reset"
docker exec -it interview_backend alembic upgrade head
```

### 3. (선택) 초기 데이터 확인
```bash
docker exec -it interview_db psql -U postgres -d interview_db -c "\dt"
```

---

## ⚠️ 주의사항
- **DB 데이터 유실**: 볼륨을 삭제했으므로 기존 데이터는 모두 사라졌습니다.
- **초기 로딩**: 첫 실행 시 모델 다운로드 등으로 인해 API 응답이 느릴 수 있습니다.
