-- ==========================================
-- 자연어DB 전문 검색 인덱스 생성 스크립트
-- PostgreSQL Full-Text Search 최적화
-- ==========================================

-- 1. 기본 인덱스 생성 (자주 검색하는 컬럼)
-- ==========================================

-- Users 테이블
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(full_name);

-- Interviews 테이블
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_position ON interviews(position);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
CREATE INDEX IF NOT EXISTS idx_interviews_created_at ON interviews(created_at);

-- Questions 테이블
CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_position ON questions(position);
CREATE INDEX IF NOT EXISTS idx_questions_company ON questions(company);
CREATE INDEX IF NOT EXISTS idx_questions_industry ON questions(industry);
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at);

-- Transcripts 테이블
CREATE INDEX IF NOT EXISTS idx_transcripts_interview_id ON transcripts(interview_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_speaker ON transcripts(speaker);
CREATE INDEX IF NOT EXISTS idx_transcripts_timestamp ON transcripts(timestamp);

-- EvaluationReports 테이블
CREATE INDEX IF NOT EXISTS idx_evaluation_reports_interview_id ON evaluation_reports(interview_id);

-- AnswerBank 테이블
CREATE INDEX IF NOT EXISTS idx_answer_bank_question_id ON answer_bank(question_id);
CREATE INDEX IF NOT EXISTS idx_answer_bank_score ON answer_bank(score);

-- 2. 복합 인덱스 (자주 함께 사용되는 컬럼)
-- ==========================================

-- Questions: 직무 + 카테고리 + 난이도
CREATE INDEX IF NOT EXISTS idx_questions_pos_cat_diff
ON questions(position, category, difficulty);

-- Questions: 회사 + 직무
CREATE INDEX IF NOT EXISTS idx_questions_company_position
ON questions(company, position);

-- Transcripts: 면접 + 화자 + 시간
CREATE INDEX IF NOT EXISTS idx_transcripts_interview_speaker_time
ON transcripts(interview_id, speaker, timestamp);

-- 3. 전문 검색 인덱스 (GIN - Generalized Inverted Index)
-- ==========================================

-- Questions 테이블: content 컬럼 전문 검색
-- 'simple' 사전 사용 (한국어 형태소 분석 없이 단순 토큰화)
CREATE INDEX IF NOT EXISTS idx_questions_content_fts
ON questions
USING gin(to_tsvector('simple', content));

-- Transcripts 테이블: text 컬럼 전문 검색
CREATE INDEX IF NOT EXISTS idx_transcripts_text_fts
ON transcripts
USING gin(to_tsvector('simple', text));

-- EvaluationReports 테이블: summary_text 컬럼 전문 검색
CREATE INDEX IF NOT EXISTS idx_evaluation_reports_summary_fts
ON evaluation_reports
USING gin(to_tsvector('simple', summary_text));

-- AnswerBank 테이블: answer_text 컬럼 전문 검색
CREATE INDEX IF NOT EXISTS idx_answer_bank_text_fts
ON answer_bank
USING gin(to_tsvector('simple', answer_text));

-- 4. 벡터 검색 인덱스 (IVFFlat - 데이터가 1000개 이상일 때)
-- ==========================================

-- Questions 테이블: embedding 컬럼 벡터 검색
-- 주의: 데이터가 충분히 쌓인 후 생성하세요 (최소 1000개 권장)
-- CREATE INDEX IF NOT EXISTS idx_questions_embedding
-- ON questions
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- AnswerBank 테이블: embedding 컬럼 벡터 검색
-- CREATE INDEX IF NOT EXISTS idx_answer_bank_embedding
-- ON answer_bank
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- 5. 부분 인덱스 (조건부 인덱스 - 특정 조건의 데이터만)
-- ==========================================

-- 활성화된 질문만 인덱싱
CREATE INDEX IF NOT EXISTS idx_questions_active
ON questions(id)
WHERE is_active = true;

-- 완료된 면접만 인덱싱
CREATE INDEX IF NOT EXISTS idx_interviews_completed
ON interviews(id, created_at)
WHERE status = 'completed';

-- 사용자 답변만 인덱싱 (AI 답변 제외)
CREATE INDEX IF NOT EXISTS idx_transcripts_user_only
ON transcripts(interview_id, timestamp)
WHERE speaker = 'User';

-- 6. 통계 정보 업데이트
-- ==========================================

ANALYZE users;
ANALYZE interviews;
ANALYZE questions;
ANALYZE transcripts;
ANALYZE evaluation_reports;
ANALYZE answer_bank;

-- 7. 인덱스 사용 통계 확인 (선택)
-- ==========================================

-- 인덱스 크기 확인
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 인덱스 사용 통계
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- ==========================================
-- 완료 메시지
-- ==========================================

DO $$
BEGIN
    RAISE NOTICE '✅ 자연어DB 인덱스 생성 완료!';
    RAISE NOTICE '📊 생성된 인덱스:';
    RAISE NOTICE '   - 기본 인덱스: 사용자, 면접, 질문, 대화 기록';
    RAISE NOTICE '   - 복합 인덱스: 자주 함께 사용되는 컬럼 조합';
    RAISE NOTICE '   - 전문 검색 인덱스: 텍스트 검색 최적화 (GIN)';
    RAISE NOTICE '   - 부분 인덱스: 조건부 데이터만 인덱싱';
    RAISE NOTICE '';
    RAISE NOTICE '💡 다음 단계:';
    RAISE NOTICE '   1. 전문 검색 테스트: SELECT * FROM questions WHERE to_tsvector(''simple'', content) @@ plainto_tsquery(''simple'', ''Python'');';
    RAISE NOTICE '   2. 인덱스 사용 확인: EXPLAIN ANALYZE SELECT ...';
    RAISE NOTICE '   3. 벡터 인덱스 생성 (데이터 1000개 이상일 때)';
END $$;
