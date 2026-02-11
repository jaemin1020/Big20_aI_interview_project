# STEP 1. Resume Load
import pdfplumber
from pathlib import Path


def safe_print(text, chunk_size=500):
    for i in range(0, len(text), chunk_size):
        print(text[i:i+chunk_size])


def load_resume():
    file_path = "/app/uploads/최승우_신입_이력서.pdf"
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            if t:
                text += t[:1000] + "\n"
            print(f"[DEBUG] page {i+1} 로드 완료")  # 어디서 멈추는지 확인용
    print("\n[STEP1] RAW RESUME LOADED\n")
    safe_print(text[:2000])  # 앞부분만 500씩 잘라서 출력


    return text



if __name__ == "__main__":
    text = load_resume()

        # 🔹 디버그: 전체 길이와 끝부분 확인
    print("[DEBUG] 전체 텍스트 길이:", len(text))
    print(text[-500:])  # 마지막 500자 출력

# pip install PyPDF2