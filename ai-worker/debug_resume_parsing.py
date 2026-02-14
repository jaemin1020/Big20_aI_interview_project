import logging
import os
import sys
import json

# 경로 설정
app_root = "/app"
backend_root = "/backend-core"
sys.path.insert(0, backend_root)
sys.path.insert(0, app_root)

from tasks.parse_resume import parse_resume_final

def debug_parse(pdf_name):
    path = os.path.join("/app/uploads", pdf_name)
    print(f"Checking path: {path}")
    print(f"Exists: {os.path.exists(path)}")
    
    if os.path.exists(path):
        data = parse_resume_final(path)
        print("--- Parsed Data ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 결과 요약 성격의 출력
        name = data.get("header", {}).get("name")
        skills = data.get("skills", [])
        print(f"\nResult Summary:")
        print(f"Name: {name}")
        print(f"Skills Found: {len(skills)}")
        print(f"Projects Found: {len(data.get('projects', []))}")
    else:
        print(f"File not found at {path}")
        # list directory to see what's there
        print(f"Directory listing for /app/uploads:")
        print(os.listdir("/app/uploads"))

if __name__ == "__main__":
    # 두 가지 버전 다 테스트
    debug_parse("김린_신입_이력서.pdf")
    debug_parse("test_resume.pdf")
