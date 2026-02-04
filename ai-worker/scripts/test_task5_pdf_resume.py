
import sys
import os

# /app 경로 추가
sys.path.append("/app")

from tasks.question_generator import QuestionGenerator
from tools.pdf_utils import extract_text_from_pdf

def test_pdf_question_generation(pdf_filename: str):
    print("=" * 60)
    print(f"🚀 [PDF Test] PDF 이력서 분석 및 질문 생성")
    print(f"File: {pdf_filename}")
    print("=" * 60)

    # 1. PDF 텍스트 추출
    pdf_path = f"/app/scripts/{pdf_filename}" # 도커 내부 경로 기준
    resume_text = extract_text_from_pdf(pdf_path)

    if not resume_text:
        print("❌ PDF에서 텍스트를 읽어오지 못했습니다. 파일 경로를 확인하거나 pypdf가 설치되었는지 확인하십시오.")
        return

    print(f"✅ 추출된 텍스트 일부 (5000자): \n{resume_text[:5000]}...")
    print("\n" + "-"*40)
    print("🔧 Generating questions from PDF content...")
    print("-" * 40)

    # 2. 질문 생성
    gen = QuestionGenerator()
    try:
        questions = gen.generate_questions_from_resume(
            resume_summary=resume_text,
            count=5
        )

        print("\n✨ [Generated Questions from PDF]:")
        for i, q in enumerate(questions, 1):
            print(f"{i}. {q}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    scripts_dir = "/app/scripts"

    # 인자로 파일명이 들어온 경우 우선 처리
    if len(sys.argv) > 1:
        target_pdf = sys.argv[1]
    else:
        # 폴더 내 모든 PDF 파일 찾기
        pdf_files = [f for f in os.listdir(scripts_dir) if f.lower().endswith(".pdf")]

        if not pdf_files:
            print(f"❌ '{scripts_dir}' 폴더 내에 PDF 파일이 없습니다.")
            print("파일을 해당 폴더에 넣고 다시 시도해 주십시오.")
            sys.exit(1)

        if len(pdf_files) == 1:
            target_pdf = pdf_files[0]
            print(f"📂 단일 PDF 발견: {target_pdf}")
        else:
            print("\n📂 분석할 PDF 파일을 선택해 주십시오:")
            for i, f in enumerate(pdf_files, 1):
                print(f"{i}. {f}")

            try:
                choice_str = input("\n번호 선택 (예: 1) [기본값 1]: ").strip()
                choice = int(choice_str) if choice_str else 1

                if 1 <= choice <= len(pdf_files):
                    target_pdf = pdf_files[choice-1]
                else:
                    print("❌ 잘못된 번호입니다. 1번을 선택합니다.")
                    target_pdf = pdf_files[0]
            except ValueError:
                print("❌ 유효하지 않은 입력입니다. 1번을 선택합니다.")
                target_pdf = pdf_files[0]

    test_pdf_question_generation(target_pdf)
