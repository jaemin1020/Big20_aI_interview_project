"""
이력서 PDF 파싱 Celery Task
"""
from celery import shared_task
from sqlmodel import Session
from db import Resume, engine
from datetime import datetime
import logging
import os
import re
import json
import pdfplumber

logger = logging.getLogger("ResumeParserTask")

# -------------------------------------------------------
# Helper Functions from step2_parse_resume.py
# -------------------------------------------------------
def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def get_row_text(row):
    return "".join([str(c) for c in row if c]).replace(" ", "")

def is_date(text):
    if not text: return False
    return bool(re.search(r'\d{4}', text))

def parse_resume_final(input_source):
    """
    input_source: PDF 파일 경로(str) 또는 이미 추출된 텍스트(str)
    """
    data = {
        "header": { "name": "", "target_company": "Unknown", "target_role": "Unknown" },
        "education": [],
        "activities": [],
        "awards": [],
        "projects": [],
        "certifications": [],
        "self_intro": []
    }

    full_text_buffer = []
    tables = []
    
    # 1. 입력값이 파일 경로인지 텍스트인지 판별
    is_file_path = False
    if isinstance(input_source, str) and input_source.strip().lower().endswith('.pdf') and os.path.exists(input_source):
        is_file_path = True
    elif len(input_source) < 300 and os.path.exists(input_source): 
         is_file_path = True

    # 2. 데이터 추출
    if is_file_path:
        try:
            with pdfplumber.open(input_source) as pdf:
                # 텍스트 추출
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text_buffer.append(text)
                # 표 추출
                for page in pdf.pages:
                    extracted = page.extract_tables()
                    if extracted:
                        tables.extend(extracted)
        except Exception as e:
            logger.warning(f"⚠️ PDF 읽기 실패 (텍스트 모드로 전환 시도): {e}")
            full_text_buffer.append(input_source)
    else:
        full_text_buffer.append(input_source)

    # 3. 표 데이터 파싱
    if tables:
        # --- Phase 1: 헤더 정보 우선 탐색 ---
        for table in tables:
            for row in table:
                safe_row = [clean_text(cell) if cell else "" for cell in row]
                for i, text in enumerate(safe_row):
                    key = text.replace(" ", "")
                    # 키-값 쌍 찾기
                    if i + 1 < len(safe_row):
                        val = safe_row[i+1] 
                        if not val and i + 2 < len(safe_row): val = safe_row[i+2]
                        
                        if val:
                            if "이름" == key: data["header"]["name"] = val
                            elif "지원회사" in key or "지원기업" in key: data["header"]["target_company"] = val
                            elif "지원직무" in key or "지원분야" in key: data["header"]["target_role"] = val

        # --- Phase 2: 섹션별 데이터 파싱 ---
        current_section = None 
        for table in tables:
            flat_table = get_row_text(table[0]) if table else ""
            if "이름" in flat_table and "지원" in flat_table: continue 

            for row in table:
                row_text = get_row_text(row)
                safe_row = [clean_text(c) if c else "" for c in row]
                
                # 섹션 감지
                if "학력" in row_text or "학교명" in row_text:
                    current_section = "education"; continue
                elif "활동" in row_text and ("내용" in row_text or "구분" in row_text):
                    current_section = "activities"; continue
                elif "수상" in row_text or ("대회" in row_text and "상" in row_text):
                    current_section = "awards"; continue
                elif "프로젝트" in row_text or "과정명" in row_text:
                    current_section = "projects"; continue
                elif "자격증" in row_text:
                    current_section = "certifications"; continue

                if "기간" in row_text and ("내용" in row_text or "학교" in row_text or "과정명" in row_text): continue
                if len(safe_row) < 2: continue

                # 데이터 매핑
                if current_section == "education":
                    val1 = safe_row[1]
                    if is_date(val1) or "고등학교" in val1: continue
                    parts = re.split(r'[—ㅡ\-]', val1)
                    school = parts[0].strip()
                    major = parts[1].strip() if len(parts) > 1 else ""
                    if school:
                        data["education"].append({
                            "period": safe_row[0], "school_name": school, "major": major,
                            "gpa": safe_row[2] if len(safe_row)>2 else "", "status": safe_row[3] if len(safe_row)>3 else ""
                        })
                elif current_section == "activities":
                    val1 = safe_row[1]
                    if not val1 or is_date(val1): continue
                    data["activities"].append({
                        "period": safe_row[0], "content": val1,
                        "role": safe_row[2] if len(safe_row)>2 else "", "organization": safe_row[3] if len(safe_row)>3 else ""
                    })
                elif current_section == "awards":
                    val1 = safe_row[1]
                    if not val1 or is_date(val1): continue
                    data["awards"].append({
                        "date": safe_row[0], "title": val1,
                        "grade": safe_row[2] if len(safe_row)>2 else "", "organization": safe_row[3] if len(safe_row)>3 else ""
                    })
                elif current_section == "projects":
                    title = safe_row[1]
                    if not title or is_date(title) or "과정명" in title: continue
                    data["projects"].append({
                        "title": title, "period": safe_row[0], "description": safe_row[2] if len(safe_row)>2 else ""
                    })
                elif current_section == "certifications":
                    v0, v1 = safe_row[0], safe_row[1] if len(safe_row)>1 else ""
                    title, date = (v1, v0) if is_date(v0) and not is_date(v1) else (v0, v1)
                    if title and not is_date(title):
                        data["certifications"].append({ "title": title, "date": date, "organization": "" })

    # 4. 자기소개서 처리 (텍스트/파일 공통)
    full_text = "\n".join(full_text_buffer)
    # 질문 패턴: [질문N] ... 주십시오/세요
    pattern = r'(\[질문\d+\].*?(?:주십시오|세요))'
    parts = re.split(pattern, full_text, flags=re.DOTALL)
    current_q = ""
    for part in parts:
        part = part.strip()
        if not part: continue
        if re.match(r'\[질문\d+\]', part) and (part.endswith("주십시오") or part.endswith("세요")):
            current_q = part
        elif current_q:
            data["self_intro"].append({"question": clean_text(current_q), "answer": part})
            current_q = ""
            
    # 원본 텍스트도 반환
    data["full_text"] = full_text
    return data

@shared_task(bind=True, name="parse_resume_pdf")
def parse_resume_pdf_task(self, resume_id: int, file_path: str):
    """
    이력서 PDF 파싱 및 구조화 Task (규칙 기반)
    
    Args:
        resume_id: Resume ID
        file_path: PDF 파일 경로
    """
    logger.info(f"[Task {self.request.id}] Resume {resume_id} 파싱 시작")
    
    try:
        # 1. Resume 레코드 조회
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found")
                return {"status": "error", "message": "Resume not found"}
            
            # 상태 업데이트: processing
            resume.processing_status = "processing"
            session.add(resume)
            session.commit()
        
        # 2. 파싱 실행 (규칙 기반)
        logger.info(f"[Resume {resume_id}] 규칙 기반 파싱 실행 중...")
        parsed_data = parse_resume_final(file_path)
        
        # 3. 데이터 매핑 및 저장
        # structured_data에 파싱 결과 저장
        # resume_embedding.py 호환성을 위해 키 매핑
        
        structured_data = {
            "target_company": parsed_data["header"].get("target_company", "Unknown"),
            "target_position": parsed_data["header"].get("target_role", "Unknown"),
            "education": parsed_data["education"],
            "experience": parsed_data["activities"], # 활동을 경력으로 매핑 (임시)
            "projects": parsed_data["projects"],
            "certifications": parsed_data["certifications"],
            "awards": parsed_data["awards"],
            "self_introduction": parsed_data["self_intro"], # 자소서
            "cover_letter": parsed_data["self_intro"], # embedding.py 호환용
            "skills": {}, # 파서에서 별도 추출 안함
            "languages": [],
            "raw_text_length": len(parsed_data.get("full_text", ""))
        }
        
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if resume:
                resume.extracted_text = parsed_data.get("full_text", "")
                resume.structured_data = structured_data
                resume.processing_status = "completed"
                resume.processed_at = datetime.utcnow()
                session.add(resume)
                session.commit()
                logger.info(f"[Resume {resume_id}] 파싱 완료 및 DB 저장")

        # 4. 임베딩 생성 태스크 트리거
        logger.info(f"[Resume {resume_id}] 섹션 임베딩 생성 태스크 시작...")
        from celery import current_app
        current_app.send_task(
            "generate_resume_embeddings",
            args=[resume_id]
        )
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "parsed_sections": list(structured_data.keys())
        }
        
    except Exception as e:
        logger.error(f"[Resume {resume_id}] 파싱 실패: {e}", exc_info=True)
        # 상태 업데이트: failed
        try:
            with Session(engine) as session:
                resume = session.get(Resume, resume_id)
                if resume:
                    resume.processing_status = "failed"
                    session.add(resume)
                    session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update resume status: {db_error}")

        return {"status": "error", "message": str(e)}

@shared_task(name="reprocess_resume")
def reprocess_resume_task(resume_id: int):
    logger.info(f"Resume {resume_id} 재처리 시작")
    with Session(engine) as session:
        resume = session.get(Resume, resume_id)
        if not resume:
            return {"status": "error", "message": "Resume not found"}
        file_path = resume.file_path
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}
    return parse_resume_pdf_task(resume_id, file_path)


# 사용 예시
if __name__ == "__main__":
    # 테스트
    result = parse_resume_pdf_task(1, "path/to/resume.pdf")
    print(result)
