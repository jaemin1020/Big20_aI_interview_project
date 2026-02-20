
import re

def is_date(text):
    if not text: return False
    return bool(re.search(r'\d{4}', text))

def test_parse_v2(safe_row, current_section, row_text):
    data = {"education": [], "activities": [], "awards": []}
    
    if current_section == "education" and len(safe_row) >= 2:
        period = safe_row[0]
        val1 = safe_row[1]
        
        major = ""
        gpa = ""
        parts = re.split(r'[—ㅡ\-\(\)]', val1)
        school = parts[0].strip()
        if len(parts) > 1: major = parts[1].strip()
        
        for cell in safe_row[2:]:
            if not cell: continue
            if any(kw in cell for kw in ["학과", "학부", "전공"]):
                major = cell.replace("학과", "").replace("전공", "").replace("학부", "").strip()
            elif re.search(r'\d\.\d|\d+/\d+', cell):
                gpa = cell
            elif not major and not re.search(r'\d', cell):
                major = cell
        
        if not gpa and len(safe_row) > 3: gpa = safe_row[3]
        
        data["education"].append({
            "period": period, "school_name": school, "major": major, "gpa": gpa
        })

    elif current_section == "activities" and len(safe_row) >= 2:
        period = safe_row[0]
        org = safe_row[1]
        role = safe_row[2] if len(safe_row) > 2 else ""
        desc = safe_row[3] if len(safe_row) > 3 else ""
        
        combined_text = org
        if " - " in combined_text or "(" in combined_text:
            date_match = re.search(r'\(([^)]*\d{4}[^)]*)\)', combined_text)
            if date_match:
                extracted_date = date_match.group(1).strip()
                if not is_date(period): period = extracted_date
                combined_text = combined_text.replace(date_match.group(0), "").strip()
            
            parts = re.split(r' [—ㅡ\-\:] | - ', combined_text)
            if len(parts) >= 2:
                org = parts[0].strip()
                if not role: role = parts[1].strip()

        if any(kw in row_text for kw in ["수상", "장려상", "우수상", "최우수상", "대상", "공모전"]):
            data["awards"].append({"date": period, "title": org, "organization": role})
        else:
            data["activities"].append({"period": period, "organization": org, "role": role, "description": desc})

    print(data)

print("--- Education GPA Fix Test ---")
test_parse_v2(["2018-2022", "한국대학교", "4.0/4.5", "졸업"], "education", "한국대학교4.0/4.5졸업")
test_parse_v2(["2018-2022", "한국대학교", "컴퓨터공학과", "4.0/4.5"], "education", "한국대학교컴퓨터공학과4.0/4.5")

print("--- Career Combination Fix Test ---")
test_parse_v2(["경력", "AWS 클라우드 기반 빅데이터 분석 및 AI 모델링 전문가 과정 - (2025년 3월 – 2025년 12월)", "", ""], "activities", "경력AWS클라우드...")
test_parse_v2(["2025.03", "제12회 공공데이터 활용 비즈니스 아이디어 공모전 - 장려상 (2025년 3월)", "", ""], "activities", "공모전장려상")
