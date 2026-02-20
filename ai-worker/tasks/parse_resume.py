import pdfplumber # PDF의 텍스트와 표를 정교하게 추출하는 라이브러리
import re         # [문법] 정규 표현식(Regular Expression): 특정 패턴의 문자열을 찾을 때 사용
import json
import os

# ==========================================
# 1. 보조 도구 함수들 (Utility Functions)
# ==========================================

def clean_text(text):
    """글자 사이의 불필요한 공백을 제거합니다."""
    if not text: return ""
    # [문법] re.sub(패턴, 바꿀글자, 원본): \s+는 '하나 이상의 공백'을 의미합니다.
    # 즉, 줄바꿈이나 여러 개의 스페이스를 딱 한 칸의 공백으로 합쳐버립니다.
    return re.sub(r'\s+', ' ', text).strip()

def get_row_text(row):
    """표의 한 줄(row)을 통째로 붙여서 하나의 문자열로 만듭니다."""
    # [문법] [str(c) for c in row if c]: 리스트 컴프리헨션. row 안에 내용(c)이 있는 것만 골라 문자열로 바꿉니다.
    return "".join([str(c) for c in row if c]).replace(" ", "")

def is_date(text):
    """해당 글자가 날짜(연도)를 포함하고 있는지 확인합니다."""
    if not text: return False
    # [문법] re.search: 패턴이 문자열 안에 있는지 확인. \d{4}는 '숫자 4개'가 연속되는지(예: 2024) 확인합니다.
    return bool(re.search(r'\d{4}', text))

# ==========================================
# 2. 메인 파싱 함수
# ==========================================

def parse_resume_final(input_source):
    # 최종 데이터를 담을 그릇 (구조화된 딕셔너리)
    data = {
        "header": { "name": "", "target_company": "", "target_role": "" },
        "education": [], "activities": [], "awards": [], "projects": [],
        "certifications": [], "self_intro": []
    }

    full_text_buffer = []
    tables = []
    
    # [해석] 입력값이 파일 경로인지 실제 텍스트인지 판별하는 똑똑한 로직입니다.
    is_file_path = False
    if isinstance(input_source, str) and input_source.strip().lower().endswith('.pdf') and os.path.exists(input_source):
        is_file_path = True
    elif len(input_source) < 300 and os.path.exists(input_source): 
         is_file_path = True

    # -------------------------------------------------------
    # PDF에서 데이터 뽑아내기
    # -------------------------------------------------------
    if is_file_path:
        try:
            with pdfplumber.open(input_source) as pdf:
                # [문법] for page in pdf.pages: PDF의 모든 페이지를 한 장씩 넘기며 읽습니다.
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text_buffer.append(text)
                
                # 표(Table) 데이터만 따로 다 추출해서 모읍니다.
                for page in pdf.pages:
                    tables.extend(page.extract_tables())
        except Exception as e:
            print(f"⚠️ PDF 읽기 실패: {e}")
            full_text_buffer.append(input_source)
    else:
        full_text_buffer.append(input_source)

    # -------------------------------------------------------
    # 데이터 분석 (표 파싱)
    # -------------------------------------------------------
    if tables:
        # [해석] Phase 1: 이름, 지원직무 같은 기본 정보(Header)를 먼저 표에서 찾습니다.
        for table in tables:
            for row in table:
                # [문법] enumerate: 리스트의 순서(i)와 내용(text)을 동시에 가져옵니다.
                safe_row = [clean_text(cell) if cell else "" for cell in row]
                for i, text in enumerate(safe_row):
                    key = text.replace(" ", "")
                    # "이름"이라는 칸을 찾으면 그 옆 칸(i+1)이 실제 이름일 확률이 높겠죠?
                    if i + 1 < len(safe_row):
                        val = safe_row[i+1] 
                        if not val and i + 2 < len(safe_row): val = safe_row[i+2]
                        
                        if val:
                            if "이름" == key: data["header"]["name"] = val
                            elif "지원회사" in key: data["header"]["target_company"] = val
                            elif "지원직무" in key: data["header"]["target_role"] = val

        # [해석] 만약 표에 이름이 없다면? 정규식(Regex)으로 텍스트 전체에서 '이름: OOO' 패턴을 찾습니다. (폴백 로직)
        full_text = "\n".join(full_text_buffer)
        if not data["header"]["name"]:
            # [문법] r"패턴": 정규식 패턴. [가-힣]{2,4}는 한국어 이름 2~4자를 의미합니다.
            name_match = re.search(r"이\s*름\s*[:：\-\s]+([가-힣]{2,4})", full_text)
            if name_match: data["header"]["name"] = name_match.group(1).strip()

        # [해석] Phase 2: 이제 본문 섹션을 나눕니다 (학력, 수상, 프로젝트 등)
        current_section = None 
        for table in tables:
            for row in table:
                row_text = get_row_text(row)
                safe_row = [clean_text(c) if c else "" for c in row]
                
                # [해석] "학력"이라는 단어가 나오면 지금부터 나오는 줄들은 다 "education"에 저장해! 라고 깃발을 꽂는 겁니다.
                if any(kw in row_text for kw in ["학력", "Education"]): current_section = "education"; continue
                elif any(kw in row_text for kw in ["경력", "경험", "활동", "Work", "Experience"]): current_section = "activities"; continue
                elif any(kw in row_text for kw in ["수상", "Awards"]): current_section = "awards"; continue
                elif any(kw in row_text for kw in ["자격증", "Certifications", "License"]): current_section = "certifications"; continue
                elif any(kw in row_text for kw in ["프로젝트", "Projects"]): current_section = "projects"; continue

                # 실제 데이터 매핑 (비어있는 행은 무시)
                if not any(safe_row): continue

                if current_section == "education" and len(safe_row) >= 2:
                    period = safe_row[0]
                    val1 = safe_row[1]
                    if is_date(val1) or "고등학교" in val1: continue # 고등학교 정보는 제외하는 필터링
                    
                    # [문법] re.split: -, ㅡ 같은 다양한 기호를 기준으로 학교명과 전공을 쪼갭니다.
                    parts = re.split(r'[—ㅡ\-]', val1)
                    school = parts[0].strip()
                    major = parts[1].strip() if len(parts) > 1 else ""
                    
                    # 만약 전공이 비어 있고 3번째 칸이 있다면 그걸 전공으로 간주해봅니다.
                    gpa = ""
                    if not major and len(safe_row) > 2:
                        major = safe_row[2]
                        gpa = safe_row[3] if len(safe_row) > 3 else ""
                    else:
                        gpa = safe_row[2] if len(safe_row) > 2 else ""
                    
                    data["education"].append({
                        "period": period, "school_name": school, "major": major, "gpa": gpa
                    })

                elif current_section == "activities" and len(safe_row) >= 2:
                    # [기간 | 기관/회사 | 역할 | 상세내용] 구조 대응
                    data["activities"].append({
                        "period": safe_row[0],
                        "organization": safe_row[1],
                        "role": safe_row[2] if len(safe_row) > 2 else "",
                        "description": safe_row[3] if len(safe_row) > 3 else ""
                    })

                elif current_section == "awards" and len(safe_row) >= 2:
                    data["awards"].append({
                        "date": safe_row[0],
                        "title": safe_row[1],
                        "organization": safe_row[2] if len(safe_row) > 2 else ""
                    })

                elif current_section == "certifications" and len(safe_row) >= 2:
                    data["certifications"].append({
                        "date": safe_row[0],
                        "title": safe_row[1],
                        "organization": safe_row[2] if len(safe_row) > 2 else ""
                    })

                elif current_section == "projects" and len(safe_row) >= 2:
                    data["projects"].append({
                        "period": safe_row[0],
                        "title": safe_row[1],
                        "description": safe_row[2] if len(safe_row) > 2 else ""
                    })

    # -------------------------------------------------------
    # 3. 자기소개서 처리 (텍스트 분석)
    # -------------------------------------------------------
    # [해석] 자소서는 표가 아니라 긴 글이므로 "[질문1] ... 하세요" 패턴을 찾아 질문과 답변을 쪼갭니다.
    full_text = "\n".join(full_text_buffer)
    # [문법] (?:주십시오|세요): '주십시오' 또는 '세요'로 끝나는 문장을 찾되, 괄호로 그룹화하지는 말라는 뜻입니다.
    pattern = r'(\[질문\d+\].*?(?:주십시오|세요))'
    parts = re.split(pattern, full_text, flags=re.DOTALL)
    
    current_q = ""
    for part in parts:
        part = part.strip()
        if not part: continue
        # 질문인지 답변인지 판별하여 리스트에 쏙쏙 넣습니다.
        if re.match(r'\[질문\d+\]', part):
            current_q = part
        elif current_q:
            data["self_intro"].append({"question": clean_text(current_q), "answer": part})
            current_q = ""

    return data