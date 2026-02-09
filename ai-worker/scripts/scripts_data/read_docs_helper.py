
from docx import Document
import json
import os

def read_docx(path):
    print(f"\n--- Reading {path} ---")
    if not os.path.exists(path):
        print("File does not exist.")
        return
    doc = Document(path)
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            print(f"[{i}] {p.text}")

def read_json_head(path, lines=20):
    print(f"\n--- Reading {path} (head) ---")
    if not os.path.exists(path):
        print("File does not exist.")
        return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(json.dumps(data[:2] if isinstance(data, list) else data, indent=2, ensure_ascii=False))

# reference 1
read_docx(r"C:\big20\git\Big20_aI_interview_project\ai-worker\scripts\scripts_data\26.01.23(금) 기업별 ‘인재상’ 의 루브릭 평가항목 기술구현.docx")

# reference 2
read_json_head(r"C:\big20\git\Big20_aI_interview_project\backend-core\data\corp_data.json")

# target
read_docx(r"C:\big20\git\Big20_aI_interview_project\ai-worker\scripts\scripts_data\권준호_파트별_진행보고서_찐최종.docx")
