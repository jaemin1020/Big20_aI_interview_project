"""
corp_data.json → companies 테이블 INSERT 스크립트
실행 위치: backend-core/ 또는 backend-core/data/
사용법: python import_corp_data.py
"""

import os
import sys
import json

# ── 로그 설정 (populate_industry_position.py 패턴) ────────────────────────
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "import_corp_log.txt")

with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("=== import_corp_data.py 시작 ===\n")


def log(msg):
    """설명:
        로그 파일과 콘솔에 동시에 메시지를 출력하는 핵심 함수.

    Args:
        msg: 출력할 메시지 (문자열로 변환 후 기록).

    Returns:
        None

    생성자: ejm
    생성일자: 2026-02-04
    """
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    print(msg)


try:
    log("패키지 로드 중...")
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    log("패키지 로드 완료")

    # .env 로드
    # backend-core/.env 먼저, 없으면 프로젝트 루트 .env
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend-core/data/
    BACKEND_DIR = os.path.dirname(BASE_DIR)               # backend-core/
    ROOT_DIR = os.path.dirname(BACKEND_DIR)               # 프로젝트 루트

    load_dotenv(os.path.join(BACKEND_DIR, ".env"))
    load_dotenv(os.path.join(ROOT_DIR, ".env"))

    # ── DB 연결 ────────────────────────────────────────────────────────────
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://admin:1234@db:5432/interview_db"
    )

    # 도커 외부(로컬)에서 실행할 경우 → localhost:15432 사용
    if "db:5432" in DATABASE_URL:
        LOCAL_DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:15432")
    else:
        LOCAL_DATABASE_URL = DATABASE_URL

    log(f"DATABASE_URL    : {DATABASE_URL}")
    log(f"LOCAL_DATABASE_URL: {LOCAL_DATABASE_URL}")

    # JSON 파일 경로
    JSON_PATH = os.path.join(BASE_DIR, "corp_data.json")

    def get_engine():
        """로컬 포트 우선, 실패 시 원본 URL"""
        try:
            eng = create_engine(LOCAL_DATABASE_URL)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            log(f"✅ DB 연결 성공 (로컬): {LOCAL_DATABASE_URL}")
            return eng
        except Exception as e:
            log(f"⚠️  로컬 연결 실패: {e}")
            log(f"   원본 URL로 재시도: {DATABASE_URL}")
            try:
                eng = create_engine(DATABASE_URL)
                with eng.connect() as conn:
                    conn.execute(text("SELECT 1"))
                log(f"✅ DB 연결 성공 (원본): {DATABASE_URL}")
                return eng
            except Exception as e2:
                log(f"❌ DB 연결 최종 실패: {e2}")
                return None

    def import_companies():
        """설명:
            corp_data.json 파일을 로드하여 companies 테이블에 UPSERT 가 포함한 복수 회사 데이터를 INSERT.

        Returns:
            None

        생성자: ejm
        생성일자: 2026-02-04
        """
        # JSON 로드
        log(f"\n📂 JSON 로드: {JSON_PATH}")
        if not os.path.exists(JSON_PATH):
            log(f"❌ 파일 없음: {JSON_PATH}")
            return

        with open(JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
        log(f"   총 {len(data)}개 기업 데이터 로드됨")

        # DB 연결
        engine = get_engine()
        if engine is None:
            log("❌ DB 연결 불가. 종료합니다.")
            return

        # INSERT
        upsert_sql = text("""
            INSERT INTO companies (id, company_name, ideal, description, created_at, updated_at)
            VALUES (:id, :company_name, :ideal, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                ideal        = EXCLUDED.ideal,
                description  = EXCLUDED.description,
                updated_at   = CURRENT_TIMESTAMP
        """)

        inserted = 0
        skipped = 0

        with engine.begin() as conn:
            for c in data:
                company_id   = str(c.get("code", "")).strip()
                company_name = str(c.get("name", "")).strip()
                ideal        = str(c.get("ideal") or "").strip()
                description  = str(c.get("description") or "").strip()

                if not company_id or not company_name:
                    log(f"  [SKIP] 필수값 누락: {c}")
                    skipped += 1
                    continue

                conn.execute(upsert_sql, {
                    "id": company_id,
                    "company_name": company_name,
                    "ideal": ideal,
                    "description": description,
                })
                inserted += 1

        log(f"\n✅ 완료! {inserted}건 UPSERT, {skipped}건 스킵")

        # 결과 확인
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            log(f"📊 companies 테이블 현재 총 {result}개 행")

    if __name__ == "__main__":
        import_companies()

except Exception as e:
    log(f"❌ CRITICAL ERROR: {e}")
    import traceback
    log(traceback.format_exc())
