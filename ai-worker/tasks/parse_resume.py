import pdfplumber
import re
import json
import os

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
        "header": { "name": "", "target_company": "", "target_role": "" },
        "education": [],
        "activities": [],
        "awards": [],
        "projects": [],
        "certifications": [],
        "self_intro": []
    }

    full_text_buffer = []
    tables = []
    
    # -------------------------------------------------------
    # 1. 입력값이 파일 경로인지 텍스트인지 판별
    # -------------------------------------------------------
    is_file_path = False
    
    # 입력값이 파일 경로처럼 생겼고(.pdf), 실제로 파일이 존재하면 -> 파일 모드
    if isinstance(input_source, str) and input_source.strip().lower().endswith('.pdf') and os.path.exists(input_source):
        is_file_path = True
    elif len(input_source) < 300 and os.path.exists(input_source): # .pdf 확장자가 없어도 파일이 있으면 경로로 간주
         is_file_path = True

    # -------------------------------------------------------
    # 2. 데이터 추출 (PDF 파일 vs 텍스트)
    # -------------------------------------------------------
    if is_file_path:
        try:
            with pdfplumber.open(input_source) as pdf:
                # 텍스트 추출
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text_buffer.append(text)
                # 표 추출
                for page in pdf.pages:
                    tables.extend(page.extract_tables())
        except Exception as e:
            print(f"⚠️ PDF 읽기 실패 (텍스트 모드로 전환 시도): {e}")
            full_text_buffer.append(input_source) # 에러나면 내용을 그냥 텍스트로 취급
    else:
        # 파일 경로가 아니라 텍스트 덩어리가 들어온 경우
        # (주의: 이 경우 표(Table) 구조는 파싱 불가능. 텍스트 기반 자소서만 파싱됨)
        full_text_buffer.append(input_source)

    # -------------------------------------------------------
    # 3. 표 데이터 파싱 (파일 모드일 때만 동작)
    # -------------------------------------------------------
    if tables:
        # --- Phase 1: 헤더 정보 우선 탐색 (표 기반) ---
        for table in tables:
            for row in table:
                safe_row = [clean_text(cell) if cell else "" for cell in row]
                for i, text in enumerate(safe_row):
                    key = text.replace(" ", "")
                    if i + 1 < len(safe_row):
                        val = safe_row[i+1] 
                        if not val and i + 2 < len(safe_row): val = safe_row[i+2]
                        
                        if val:
                            if "이름" == key: data["header"]["name"] = val
                            elif "지원회사" in key or "지원기업" in key: data["header"]["target_company"] = val
                            elif "지원직무" in key or "지원분야" in key: data["header"]["target_role"] = val

        # --- Phase 1.5: Regex 기반 폴백 (표에서 못 찾았을 때) ---
        full_text = "\n".join(full_text_buffer)
        
        # 이름 찾기
        if not data["header"]["name"]:
            name_patterns = [
                r"이\s*름\s*[:：\-\s]+([가-힣]{2,4})",
                r"성\s*함\s*[:：\-\s]+([가-힣]{2,4})",
                r"Name\s*[:：\-\s]+([a-zA-Z가-힣\s]+)"
            ]
            for p in name_patterns:
                match = re.search(p, full_text, re.IGNORECASE)
                if match:
                    data["header"]["name"] = match.group(1).strip()
                    break
        
        # 지원직무 찾기
        if not data["header"]["target_role"]:
            role_patterns = [
                r"지원\s*직무\s*[:：\-\s]+([^\n]+)",
                r"지원\s*분야\s*[:：\-\s]+([^\n]+)",
                r"희망\s*직무\s*[:：\-\s]+([^\n]+)",
                r"Position\s*[:：\-\s]+([^\n]+)",
                r"Role\s*[:：\-\s]+([^\n]+)"
            ]
            for p in role_patterns:
                match = re.search(p, full_text, re.IGNORECASE)
                if match:
                    role = re.sub(r'[\(\)\[\]]', '', match.group(1)).strip()
                    data["header"]["target_role"] = role
                    break

        # 기본값 설정
        if not data["header"]["target_role"]:
            data["header"]["target_role"] = "일반"

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

    # -------------------------------------------------------
    # 4. 자기소개서 처리 (텍스트/파일 공통)
    # -------------------------------------------------------
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

    return data

# 테스트 실행 코드
if __name__ == "__main__":
    pdf_filename = "resume.pdf"
    if os.path.exists(pdf_filename):
        try:
            print(f"🚀 '{pdf_filename}' 파싱 시작...")
            result = parse_resume_final(pdf_filename)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            with open("parsed_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("✅ 완료!")
        except Exception as e:
            print(f"💥 에러: {e}")
    else:
        print("❌ 파일 없음")


