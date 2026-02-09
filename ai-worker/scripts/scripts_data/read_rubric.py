from docx import Document

doc = Document(r"C:\big20\git\Big20_aI_interview_project\ai-worker\scripts\scripts_data\26.01.23(금) 기업별 '인재상' 의 루브릭 평가항목 기술구현.docx")

print("=== 루브릭 문서 내용 ===\n")
for i, para in enumerate(doc.paragraphs):
    if para.text.strip():
        print(f"[{i}] {para.text}")
        if i > 100:  # 처음 100개 단락만
            print("\n... (truncated)")
            break
