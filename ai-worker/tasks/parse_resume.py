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
                
                # [해석] 섹션 전환 깃발 꽂기
                if any(kw in row_text for kw in ["학력", "Education"]): current_section = "education"; continue
                elif any(kw in row_text for kw in ["경력", "경험", "활동", "Work", "Experience"]): 
                    # 만약 현재 줄에 '수상'이나 '공모전' 단어가 포함되어 있다면 수상 섹션으로 양보합니다.
                    if any(kw in row_text for kw in ["수상", "공모전", "대회", "Awards"]):
                        current_section = "awards"
                    else:
                        current_section = "activities"
                    continue
                elif any(kw in row_text for kw in ["수상", "Awards", "상훈", "공모전", "대회"]): current_section = "awards"; continue
                elif any(kw in row_text for kw in ["자격증", "Certifications", "License"]): current_section = "certifications"; continue
                elif any(kw in row_text for kw in ["프로젝트", "Projects"]): current_section = "projects"; continue

                # 실제 데이터 매핑 (비어있는 행이나 템플릿 가이드 텍스트 무시)
                # [수정] 학력 헤더 행("재학기간", "학교명") 및 활동 헤더 행도 함께 제외
                if not any(safe_row) or any(kw in row_text for kw in ["개최명", "상세내용", "활동내용", "재학기간", "학교명및전공", "학교명"]):
                    continue

                if current_section == "education" and len(safe_row) >= 2:
                    period = safe_row[0]
                    val1 = safe_row[1]
                    if is_date(val1) or "고등학교" in val1: continue # 고등학교 정보는 제외하는 필터링
                    
                    major = ""
                    gpa = ""
                    # 1. 학교명/전공 쪼개기 시도
                    parts = re.split(r'[—ㅡ\-\(\)]', val1)
                    school = parts[0].strip()
                    if len(parts) > 1: major = parts[1].strip()
                    
                    # 2. 나머지 칸에서 전공/학점 보강
                    for cell in safe_row[2:]:
                        if not cell: continue
                        if any(kw in cell for kw in ["학과", "학부", "전공"]):
                            major = cell.replace("학과", "").replace("전공", "").replace("학부", "").strip()
                        elif re.search(r'\d\.\d|\d+/\d+', cell):
                            gpa = cell
                        elif not major and not re.search(r'\d', cell):
                            major = cell
                    
                    # 3. 뒤늦게라도 학점이 발견되지 않았다면 4번째 칸 시도 (기존 호환성)
                    if not gpa and len(safe_row) > 3: gpa = safe_row[3]
                    
                    data["education"].append({
                        "period": period, "school_name": school, "major": major, "gpa": gpa
                    })

                elif current_section == "activities" and len(safe_row) >= 2:
                    period = safe_row[0]
                    org = safe_row[1]
                    role = safe_row[2] if len(safe_row) > 2 else ""
                    desc = safe_row[3] if len(safe_row) > 3 else ""
                    
                    # [보강] 단일 셀 복합 정보 쪼개기 (예: 개최명 - 점수 (기간))
                    combined_text = org
                    if " - " in combined_text or "(" in combined_text:
                        # 1. 날짜 추출
                        date_match = re.search(r'\(([^)]*\d{4}[^)]*)\)', combined_text)
                        if date_match:
                            extracted_date = date_match.group(1).strip()
                            if not is_date(period): period = extracted_date
                            combined_text = combined_text.replace(date_match.group(0), "").strip()
                        
                        # 2. 개최명/점수 쪼개기
                        parts = re.split(r' [—ㅡ\-\:] | - ', combined_text)
                        if len(parts) >= 2:
                            org = parts[0].strip()
                            if not role: role = parts[1].strip()

                    # 수상 관련 텍스트가 경력으로 들어오지 못하게 한 번 더 체크
                    if any(kw in row_text for kw in ["수상", "장려상", "우수상", "최우수상", "대상", "공모전"]):
                        data["awards"].append({
                            "date": period,
                            "title": org,
                            "organization": role
                        })
                    else:
                        # 사용자 지정 포맷 반영: 0:기간, 1:프로젝트명, 2:역할(인턴 등), 3:기관(하이브본사 등)
                        data["activities"].append({
                            "period": period,
                            "title": safe_row[1] if len(safe_row) > 1 else "",
                            "role": safe_row[2] if len(safe_row) > 2 else "",
                            "organization": safe_row[3] if len(safe_row) > 3 else ""
                        })

                elif current_section == "awards" and len(safe_row) >= 2:
                    date = safe_row[0]
                    title = safe_row[1]
                    org = safe_row[2] if len(safe_row) > 2 else ""

                    # [보강] 단일 셀 복합 정보 쪼개기
                    if " - " in title or "(" in title:
                        date_match = re.search(r'\(([^)]*\d{4}[^)]*)\)', title)
                        if date_match:
                            extracted_date = date_match.group(1).strip()
                            if not is_date(date): date = extracted_date
                            title = title.replace(date_match.group(0), "").strip()
                        
                        parts = re.split(r' [—ㅡ\-\:] | - ', title)
                        if len(parts) >= 2:
                            title = parts[0].strip()
                            if not org: org = parts[1].strip()

                    data["awards"].append({
                        "date": date, "title": title, "organization": org
                    })

                elif current_section == "certifications" and len(safe_row) >= 2:
                    data["certifications"].append({
                        "date": safe_row[0],
                        "title": safe_row[1],
                        "organization": safe_row[2] if len(safe_row) > 2 else ""
                    })

                elif current_section == "projects" and len(safe_row) >= 2:
                    # 사용자 지정 포맷 반영: 0:기간, 1:과정명/제목, 2:기관/장소
                    data["projects"].append({
                        "period": safe_row[0],
                        "title": safe_row[1],
                        "organization": safe_row[2] if len(safe_row) > 2 else ""
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