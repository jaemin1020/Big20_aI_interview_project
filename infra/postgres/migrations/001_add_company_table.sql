-- ==========================================
-- Company 테이블 추가 마이그레이션 (간소화 버전)
-- 실행 날짜: 2026-01-28
-- ==========================================

-- 1. Company 테이블 생성
CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ideal TEXT,
    description TEXT,
    embedding vector(768),  -- pgvector 타입
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name);

-- 3. 벡터 유사도 검색을 위한 인덱스 (IVFFlat)
-- 데이터가 충분히 쌓인 후 실행 권장 (최소 1000개 이상)
-- CREATE INDEX IF NOT EXISTS idx_companies_embedding ON companies 
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 4. job_postings 테이블에 company_id 컬럼 추가
ALTER TABLE job_postings 
ADD COLUMN IF NOT EXISTS company_id VARCHAR(50) REFERENCES companies(id);

CREATE INDEX IF NOT EXISTS idx_job_postings_company ON job_postings(company_id);

-- 5. updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_company_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_company_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_company_updated_at();


-- 7. 통계 수집
ANALYZE companies;

-- ==========================================
-- 마이그레이션 완료 메시지
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE '✅ Company 테이블 마이그레이션 완료';
    RAISE NOTICE '📊 Fields: id, company_name, ideal, description, embedding';
    RAISE NOTICE '🔗 Relationships: companies -> job_postings';
END $$;

