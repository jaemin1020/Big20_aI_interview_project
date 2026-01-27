-- ==========================================
-- AI Interview System - PostgreSQL 초기화 스크립트
-- Vector DB 지원 (pgvector)
-- ==========================================

-- 1. 필수 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. 인덱스 최적화를 위한 설정
SET maintenance_work_mem = '256MB';

-- 3. 테이블은 SQLModel이 자동 생성하지만, 추가 인덱스와 제약조건을 여기서 설정

-- 3. 테이블은 SQLModel이 자동 생성하므로, 인덱스 생성은 생략하거나 별도 마이그레이션으로 처리합니다.

-- 4. Vector 유사도 검색을 위한 준비 (추후 확장용)
-- Questions 테이블에 embedding 컬럼 추가 (선택적)
-- ALTER TABLE questions ADD COLUMN IF NOT EXISTS embedding vector(1536);
-- CREATE INDEX IF NOT EXISTS idx_questions_embedding ON questions USING ivfflat (embedding vector_cosine_ops);

-- 5. 트리거 설정 (자동 타임스탬프 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Evaluation_Reports의 updated_at 자동 업데이트 트리거
CREATE TRIGGER update_evaluation_reports_updated_at 
    BEFORE UPDATE ON evaluation_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 6. 샘플 데이터 삽입 (선택적 - 개발용)
-- INSERT INTO job_postings (title, description, requirements, position)
-- VALUES 
--     ('Senior Backend Developer', 'Join our team!', 'Python, FastAPI, PostgreSQL', 'Backend Developer'),
--     ('Frontend Engineer', 'Build amazing UIs', 'React, TypeScript, Vite', 'Frontend Developer')
-- ON CONFLICT DO NOTHING;

-- 7. 통계 수집 (성능 최적화)
ANALYZE users;
ANALYZE interviews;
ANALYZE questions;
ANALYZE transcripts;
ANALYZE evaluation_reports;

-- ==========================================
-- 초기화 완료 메시지
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE '✅ AI Interview Database initialized successfully';
    RAISE NOTICE '📊 Tables: users, interviews, questions, transcripts, evaluation_reports';
    RAISE NOTICE '🔍 Extensions: vector, uuid-ossp';
END $$;