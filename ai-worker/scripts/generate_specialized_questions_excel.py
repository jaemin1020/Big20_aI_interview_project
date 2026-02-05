
import os
import pandas as pd
import logging
from langchain_community.llms import LlamaCpp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExcelGen")

MODEL_PATH = os.getenv("EVALUATOR_MODEL_PATH", "/app/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
INPUT_FILE = 'scripts/llm_test_data.xlsx'
OUTPUT_FILE = 'scripts/llm_test_data_with_questions.xlsx'
QUESTIONS_PER_ITEM = 3

def load_model():
    logger.info(f"Loading model from {MODEL_PATH}")
    return LlamaCpp(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=6,
        n_gpu_layers=0,
        temperature=0.7,
        max_tokens=512,
        verbose=False
    )

def generate_questions(llm, resume_summary, original_question):
    prompt = f"""다음은 지원자의 이력서 요약입니다:

{resume_summary}

다음은 참고할 원본 면접 질문입니다:
"{original_question}"

**중요**: 위 원본 질문의 주제와 의도를 반드시 유지하면서, 이 지원자의 이력서 내용에 맞게 구체화한 질문을 {QUESTIONS_PER_ITEM}개 생성해주세요.

예시:
원본: "자기소개를 해보세요" → 생성: "보안 엔지니어로서의 경력과 KISA 인턴 경험을 중심으로 자기소개를 해주세요"
원본: "프로젝트 경험은?" → 생성: "Snort를 활용한 IDS 구축 프로젝트에서 어떤 역할을 맡으셨나요?"

**반드시 원본 질문의 핵심 주제를 유지하면서** 이력서의 구체적인 내용(프로젝트명, 기술명, 경험 등)을 포함해주세요.

형식:
1. [질문]
2. [질문]
3. [질문]

예상 질문:"""

    try:
        response = llm.invoke(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return ""

def main():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        return

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read excel: {e}")
        return

    llm = load_model()

    generated_results = []

    # Check columns
    # Mapped: 'question' -> Original Question, 'answer' -> Resume Summary

    print("Processing rows...")
    for index, row in df.iterrows():
        original_q = row.get('question', '')
        resume_sum = row.get('answer', '') # Assuming 'answer' serves as resume context

        if pd.isna(original_q) or pd.isna(resume_sum):
            generated_results.append("")
            continue

        print(f"Processing row {index+1}/{len(df)}...")
        result = generate_questions(llm, resume_sum, original_q)
        generated_results.append(result)

    df['generated_questions_raw'] = generated_results

    # Save output
    df.to_excel(OUTPUT_FILE, index=False)
    logger.info(f"Saved results to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
