# ⚠️ DEPRECATED - 이 파일은 더 이상 사용되지 않습니다
# 질문 생성 로직은 ai-worker/tasks/question_generator.py로 이동되었습니다.
# 
# 이유:
# 1. Backend 부팅 시간 단축 (모델 로딩 제거)
# 2. GPU 리소스 효율적 관리 (AI-Worker에서 통합 관리)
# 3. 확장성 향상 (Celery를 통한 비동기 처리)
# 4. 아키텍처 일관성 (모든 AI 작업을 AI-Worker에서 처리)
#
# 마이그레이션 날짜: 2026-01-21
# 참조: ai-worker/tasks/question_generator.py

# 원본 코드는 참조용으로 보존됨
