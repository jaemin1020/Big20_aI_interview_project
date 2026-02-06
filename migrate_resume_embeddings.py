import os
import json
import sys
from sqlmodel import Session, create_engine, select, text
from dotenv import load_dotenv
from typing import Dict, Any, List

# backend-core 경로 추가 (models.py 임포트를 위해)
sys.path.append(os.path.join(os.getcwd(), "backend-core"))
from models import User, Resume, ResumeChunk, SectionType, UserRole

# .env 로드
load_dotenv()

# DB 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
if "db:5432" in DATABASE_URL:
    LOCAL_DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:15432")
else:
    LOCAL_DATABASE_URL = DATABASE_URL

print(f"[*] Connecting to database at {LOCAL_DATABASE_URL}...")
engine = create_engine(LOCAL_DATABASE_URL)

# 텍스트 직렬화 함수 (embedding.py와 동일하게 구현)
def serialize_profile(profile):
    return f"이름: {profile.get('name','')}\n지원직무: {profile.get('target_position','')}\n지원회사: {profile.get('target_company','')}".strip()

def serialize_experience(exp):
    return f"회사: {exp.get('company','')}\n역할: {exp.get('role','')}\n내용: {exp.get('description','')}".strip()

def serialize_project(proj):
    return f"프로젝트명: {proj.get('title','')}\n내용: {proj.get('description','')}".strip()

def serialize_self_intro(si):
    return f"질문: {si.get('question','')}\n답변: {si.get('answer','')}".strip()

def migrate():
    # 1. 파일 로드
    structured_file = "resume_structured.json"
    embeddings_file = "resume_multi_embeddings.json"

    if not os.path.exists(structured_file) or not os.path.exists(embeddings_file):
        print(f"[!] Error: Files not found. ({structured_file}, {embeddings_file})")
        return

    with open(structured_file, "r", encoding="utf-8") as f:
        resume_data = json.load(f)
    
    with open(embeddings_file, "r", encoding="utf-8") as f:
        embedding_data = json.load(f)

    with Session(engine) as session:
        # 0. pgvector 확장 활성화
        print("[*] Enabling pgvector extension...")
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()

        # 2. 더미 사용자 확인 또는 생성
        user_email = "sw_choi@example.com"
        statement = select(User).where(User.email == user_email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"[*] Creating dummy user: {user_email}")
            user = User(
                email=user_email,
                username="choi_sw",
                password_hash="hashed_password",
                full_name="최승우",
                role=UserRole.CANDIDATE
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # 3. 이력서 레코드 생성
        print(f"[*] Creating/Updating resume record for user {user.id}...")
        resume = Resume(
            candidate_id=user.id,
            file_name="AI 이력서(1) 최승우_수정.pdf",
            file_path="uploads/res_001.pdf",
            file_size=169285,
            structured_data=resume_data,
            processing_status="completed"
        )
        session.add(resume)
        session.commit()
        session.refresh(resume)
        
        print(f"[*] Resume ID: {resume.id}")

        # 4. 섹션별 청크 및 벡터 삽입
        chunks_to_add = []
        
        # --- Profile ---
        profile_text = serialize_profile(resume_data["profile"])
        profile_vector = embedding_data["embeddings"]["profile"]["vector"]
        chunks_to_add.append(ResumeChunk(
            resume_id=resume.id,
            content=profile_text,
            chunk_index=0,
            section_type=SectionType.TARGET_INFO,
            embedding=profile_vector
        ))
        
        # --- Experience ---
        for idx, (exp, emb) in enumerate(zip(resume_data.get("experience", []), embedding_data["embeddings"]["experience"]), start=1):
            chunk_content = serialize_experience(exp)
            chunks_to_add.append(ResumeChunk(
                resume_id=resume.id,
                content=chunk_content,
                chunk_index=idx,
                section_type=SectionType.CAREER_PROJECT,
                embedding=emb["vector"]
            ))
            
        # --- Projects ---
        start_idx = len(chunks_to_add)
        for idx, (proj, emb) in enumerate(zip(resume_data.get("projects", []), embedding_data["embeddings"]["projects"]), start=start_idx):
            chunk_content = serialize_project(proj)
            chunks_to_add.append(ResumeChunk(
                resume_id=resume.id,
                content=chunk_content,
                chunk_index=idx,
                section_type=SectionType.CAREER_PROJECT,
                embedding=emb["vector"]
            ))

        # --- Self Introduction ---
        start_idx = len(chunks_to_add)
        for idx, (si, emb) in enumerate(zip(resume_data.get("self_introduction", []), embedding_data["embeddings"]["self_introduction"]), start=start_idx):
            chunk_content = serialize_self_intro(si)
            chunks_to_add.append(ResumeChunk(
                resume_id=resume.id,
                content=chunk_content,
                chunk_index=idx,
                section_type=SectionType.COVER_LETTER,
                embedding=emb["vector"]
            ))

        print(f"[*] Adding {len(chunks_to_add)} resume chunks to database...")
        for chunk in chunks_to_add:
            session.add(chunk)
        
        session.commit()
        print("[+] Migration completed successfully!")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"[!] Critical Error: {e}")
        import traceback
        traceback.print_exc()
