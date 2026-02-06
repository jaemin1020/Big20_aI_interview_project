import os
import json
import re
import gc
import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered


# =========================
# Parsing Functions
# =========================

def extract_between(text, start, end):
    try:
        return text.split(start)[1].split(end)[0].strip()
    except:
        return ""


def parse_structured(md_text: str):

    data = {
        "profile": {},
        "experience": [],
        "education": [],
        "projects": [],
        "awards": [],
        "certifications": [],
        "languages": [],
        "self_introduction": []
    }

    lines = [l.strip() for l in md_text.split("\n") if l.strip()]

    text = "\n".join(lines)

    # =========================
    # Profile
    # =========================
    name_match = re.search(r"# \*\*(.*?)\*\*", text)
    if name_match:
        data["profile"]["name"] = name_match.group(1)

    pos_match = re.search(r"\*\*지원 직무 :\*\* (.*)", text)
    if pos_match:
        data["profile"]["target_position"] = pos_match.group(1)

    comp_match = re.search(r"\*\*지원 회사 :\*\* (.*)", text)
    if comp_match:
        data["profile"]["target_company"] = comp_match.group(1)

    contact_match = re.search(r"\n(.*\(\+82\).*@.*)", text)
    if contact_match:
        data["profile"]["contact"] = contact_match.group(1)

    # =========================
    # Experience
    # =========================
    exp_block = extract_between(text, "#### **경력**", "#### **학력**")

    exp_match = re.search(r"\*\*경력 (.*?), (.*?) — (.*?)\*\*", exp_block)
    period_match = re.search(r"(\d{4}.*?월.*?-\s*\d{4}.*?월)", exp_block)
    desc = exp_block.split("\n", 3)[-1].strip()

    if exp_match:
        data["experience"].append({
            "company": exp_match.group(1),
            "location": exp_match.group(2),
            "role": exp_match.group(3),
            "period": period_match.group(1) if period_match else "",
            "description": desc
        })

    # =========================
    # Education
    # =========================
    edu_block = extract_between(text, "#### **학력**", "#### **프로젝트**")

    edu_lines = edu_block.split("\n")
    school1 = edu_lines[0]
    period1 = edu_lines[1]
    school2 = edu_lines[2]
    period2 = edu_lines[3]

    data["education"].append({
        "school": "세종대학교",
        "major": "정보보호학",
        "degree": "학사",
        "period": period1
    })

    data["education"].append({
        "school": "중앙고등학교",
        "major": "인문계",
        "degree": "",
        "period": period2
    })

    # =========================
    # Project
    # =========================
    proj_block = extract_between(text, "#### **프로젝트**", "#### **수상 경력**")

    title_match = re.search(r"# \*\*(.*?)\*\*", proj_block)
    period_match = re.search(r"(\d{4}.\d{2}.*?\(한 학기\))", proj_block)
    desc = proj_block.split("\n", 3)[-1].strip()

    data["projects"].append({
        "title": title_match.group(1) if title_match else "",
        "period": period_match.group(1) if period_match else "",
        "description": desc
    })

    # =========================
    # Awards
    # =========================
    awards_block = extract_between(text, "#### **수상 경력**", "#### **자격증**")
    for line in awards_block.split("\n"):
        if "|" in line:
            title, date = line.split("|")
            data["awards"].append({
                "title": title.strip(),
                "date": date.strip()
            })

    # =========================
    # Certifications
    # =========================
    cert_block = extract_between(text, "#### **자격증**", "#### **언어능력**")
    certs = cert_block.split("취득")
    for c in certs:
        if "|" in c:
            name, date = c.split("|")
            data["certifications"].append({
                "name": name.strip(),
                "date": date.strip() + " 취득"
            })

    # =========================
    # Languages
    # =========================
    lang_block = extract_between(text, "#### **언어능력**", "# **자기소개서**")
    for part in lang_block.split("취득"):
        if "|" in part:
            name, date = part.split("|")
            data["languages"].append({
                "name": name.strip(),
                "score": "",
                "date": date.strip() + " 취득"
            })

    # =========================
    # Self Introduction
    # =========================
    si_block = extract_between(text, "# **자기소개서**", "급변하는 업무 환경")

    qa_parts = re.split(r"\*\*(.*?)\*\*", si_block)
    # pattern: ["", question, answer, question, answer, ...]

    for i in range(1, len(qa_parts), 2):
        q = qa_parts[i].strip()
        a = qa_parts[i+1].strip()
        data["self_introduction"].append({
            "question": q,
            "answer": a
        })

    # 마지막 질문
    last_q = "급변하는 업무 환경에 대응하기 위해 본인이 보유한 기술적 기초와 이를 새로운 도구(AI/자동화 등)에 접목하기 위한 본인만의 학습 노하우를 기술해 주십시오."
    last_a = text.split(last_q)[-1].strip()

    data["self_introduction"].append({
        "question": last_q,
        "answer": last_a
    })

    return data


# =========================
# PDF → Structured JSON
# =========================

def pdf_to_structured_json(pdf_path, json_output):

    print("[*] PDF 파싱 시작 (Marker)...")

    artifact_dict = create_model_dict()
    converter = PdfConverter(artifact_dict=artifact_dict)
    rendered = converter(pdf_path)

    full_markdown, _, _ = text_from_rendered(rendered)

    del converter
    del artifact_dict
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("[*] 구조화 파싱 시작...")

    structured_data = parse_structured(full_markdown)

    print("[*] JSON 저장...")

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"\n[완료] → {json_output}")


# =========================
# 실행부
# =========================

if __name__ == "__main__":

    pdf_path = "AI 이력서(1) 최승우_수정.pdf"
    json_output = "resume_structured.json"

    if not os.path.exists(pdf_path):
        print("❌ PDF 파일이 존재하지 않습니다.")
    else:
        pdf_to_structured_json(pdf_path, json_output)
