
import re

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def is_date(text):
    if not text: return False
    return bool(re.search(r'\d{4}', text))

def test_parse(safe_row, section):
    row_text = "".join([str(c) for c in safe_row if c]).replace(" ", "")
    
    if section == "education":
        period = safe_row[0]
        val1 = safe_row[1]
        parts = re.split(r'[—ㅡ\-\(\)]', val1)
        school = parts[0].strip()
        major = parts[1].strip() if len(parts) > 1 else ""
        
        if not major:
            for cell in safe_row[2:]:
                if any(kw in cell for kw in ["학과", "학부", "전공"]):
                    major = cell.replace("학과", "").replace("전공", "").replace("학부", "").strip()
                    break
        
        if not major and len(safe_row) > 2:
            major = safe_row[2]
            
        print(f"Education: Period={period}, School={school}, Major={major}, GPA={safe_row[3] if len(safe_row) > 3 else ''}")

    elif section == "activities":
        if any(kw in row_text for kw in ["수상", "장려상", "우수상", "최우수상", "대상", "공모전"]):
            # Awards logic
            print(f"Award: Date={safe_row[0]}, Title={safe_row[1]}, Org={safe_row[2] if len(safe_row) > 2 else ''}")
        else:
            # Activities logic
            print(f"Activity: Period={safe_row[0]}, Org={safe_row[1]}, Role={safe_row[2] if len(safe_row) > 2 else ''}, Desc={safe_row[3] if len(safe_row) > 3 else ''}")

print("--- Current Logic Test ---")
test_parse(["2025.03-2025.12", "AWS 클라우드 기반 빅데이터 분석 및 AI 모델링 전문가 과정", "", ""], "activities")
test_parse(["2025.03", "제12회 공공데이터 활용 비즈니스 아이디어 공모전 - 장려상", "", ""], "activities")
test_parse(["2018-2022", "한국대학교", "4.0/4.5", "졸업"], "education")
