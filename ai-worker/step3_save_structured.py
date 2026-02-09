import sys
import os
import json
from sqlalchemy import text as sql_text

# -----------------------------------------------------------
# [경로 설정] backend-core 및 ai-worker 폴더 인식
# -----------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_core_docker = "/backend-core"
backend_core_local = os.path.join(current_dir, "backend-core")

if os.path.exists(backend_core_docker):
    sys.path.append(backend_core_docker)
elif os.path.exists(backend_core_local):
    sys.path.append(backend_core_local)
else:
    print("⚠️ backend-core 경로를 찾을 수 없습니다. 모델 import 실패 가능.")

# 🚨 db.py에서 engine 불러오기
try:
    from db import engine
except ImportError as e:
    print(f"❌ db.py를 불러오는데 실패했습니다: {e}")
    sys.exit(1)

# -----------------------------------------------------------
# 구조화 이력서 PostgreSQL 저장
# -----------------------------------------------------------
def save_structured(resume_id: int, candidate_id: int, parsed_data: dict, file_name: str):
    # 실제 파일 경로 (Docker 컨테이너 기준)
    file_path = f"/app/{file_name}" if os.path.exists(f"/app/{file_name}") else f"/app/resume.pdf"
    
    # 파일 크기 계산
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    # extracted_text: 검색용 텍스트 (이름이나 자기소개서 앞부분 등)
    # 여기서는 파싱된 이름이나 전체 JSON을 문자열로 저장
    header_info = parsed_data.get("header", {})
    extracted_text = f"{header_info.get('name', '')} {header_info.get('target_role', '')}"

    try:
        with engine.begin() as conn:
            sql = sql_text("""
                INSERT INTO resumes (
                    id, candidate_id, file_name, file_path, file_size, extracted_text,
                    structured_data, uploaded_at, is_active, processing_status
                )
                VALUES (
                    :id, :candidate_id, :file_name, :file_path, :file_size, :extracted_text,
                    :data, CURRENT_TIMESTAMP, TRUE, 'completed'
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    structured_data = :data,
                    candidate_id = :candidate_id,
                    file_name = :file_name,
                    file_path = :file_path,
                    file_size = :file_size,
                    extracted_text = :extracted_text,
                    uploaded_at = CURRENT_TIMESTAMP,
                    is_active = TRUE,
                    processing_status = 'completed';
            """)

            json_str = json.dumps(parsed_data, ensure_ascii=False)
            conn.execute(sql, {
                "id": resume_id,
                "candidate_id": candidate_id,
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "extracted_text": extracted_text,
                "data": json_str
            })

            print(f"\n[STEP3] ✅ PostgreSQL 저장 완료 (ID: {resume_id}, candidate_id: {candidate_id}, file_name: {file_name})")

    except Exception as e:
        print(f"\n❌ DB 저장 실패: {e}")


# -----------------------------------------------------------
# 메인 실행: 파일 경로 전달 → 파싱 → DB 저장
# -----------------------------------------------------------
if __name__ == "__main__":
    try:
        # load_resume는 삭제 (이제 필요 없음)
        from step2_parse_resume import parse_resume_final
    except ImportError as e:
        print(f"❌ 필요한 모듈 import 실패: {e}")
        sys.exit(1)

    print("--- 데이터 파싱 시작 ---")
    
    # [핵심 변경] 텍스트를 읽어오는 게 아니라, '파일 경로'를 지정합니다.
    # 컨테이너 내부에 파일이 있는지 확인
    target_pdf_path = "resume.pdf"
    if not os.path.exists(target_pdf_path):
        target_pdf_path = "/app/resume.pdf"
    
    if not os.path.exists(target_pdf_path):
        print(f"❌ 오류: '{target_pdf_path}' 파일을 찾을 수 없습니다.")
        sys.exit(1)

    # 1. 파일 경로를 step2 함수에 전달 (이제 step2가 알아서 파일을 엽니다)
    print(f"📂 파일 경로 전달: {target_pdf_path}")
    parsed = parse_resume_final(target_pdf_path)
    
    if not parsed:
        print("❌ 파싱된 데이터가 없습니다.")
        sys.exit(1)

    # 파싱 결과 일부 출력 확인
    print("\n[파싱 결과 요약]")
    print(f"이름: {parsed.get('header', {}).get('name')}")
    print(f"지원직무: {parsed.get('header', {}).get('target_role')}")
    print(f"학력 수: {len(parsed.get('education', []))}")
    print(f"자소서 항목 수: {len(parsed.get('self_intro', []))}")

    # 2. DB 저장
    # 테스트용 ID (정수형) + candidate_id (정수형)
    save_structured(
        resume_id=1,
        candidate_id=1,
        parsed_data=parsed,
        file_name="resume.pdf" # 실제 저장된 파일명과 일치시키는 것이 좋음
    )