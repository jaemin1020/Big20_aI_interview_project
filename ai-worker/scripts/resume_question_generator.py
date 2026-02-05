import pandas as pd
import requests
import PyPDF2
import time

print("=" * 60)
print("📄 이력서 기반 맞춤형 예상질문 생성기 (기본 버전)")
print("=" * 60)

# ========== 설정 ==========
PDF_PATH = "AI 이력서(1) 최승우.pdf"
EXCEL_PATH = "llm_test_data.xlsx"
OUTPUT_PATH = "resume_based_questions.xlsx"
SERVER_URL = "http://localhost:8000/chat"

QUESTIONS_PER_ITEM = 3  # 각 질문당 생성할 개수

# ========== 1. PDF 이력서 읽기 ==========
print("\n📄 Step 1: PDF 이력서 읽기...")
try:
    with open(PDF_PATH, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
    
    print(f"   ✅ 이력서 로드 완료!")
    print(f"   📝 총 글자 수: {len(resume_text)}")
    print(f"   📄 미리보기: {resume_text[:200]}...")
except Exception as e:
    print(f"   ❌ 오류: {e}")
    exit(1)

# 이력서 요약 (1000자로 제한)
resume_summary = resume_text[:1000]

# ========== 2. 엑셀 질문 데이터 읽기 ==========
print("\n📊 Step 2: 엑셀 질문 데이터 읽기...")
try:
    df = pd.read_excel(EXCEL_PATH)
    print(f"   ✅ 엑셀 로드 완료!")
    print(f"   📋 열 이름: {list(df.columns)}")
    
    # 'question' 열 찾기
    if 'question' not in df.columns:
        print(f"   ⚠️  'question' 열을 찾을 수 없습니다. 사용 가능한 열: {list(df.columns)}")
        question_col = df.columns[1]  # 두 번째 열 사용
        print(f"   ℹ️  '{question_col}' 열을 질문 열로 사용합니다.")
    else:
        question_col = 'question'
    
    questions = df[question_col].dropna().tolist()
    print(f"   📝 총 질문 수: {len(questions)}")
    print(f"   📄 질문 예시:")
    for i, q in enumerate(questions[:3], 1):
        print(f"      {i}. {q}")
except Exception as e:
    print(f"   ❌ 오류: {e}")
    exit(1)

# ========== 3. 각 질문별로 LLM에게 3개씩 생성 요청 ==========
print(f"\n🤖 Step 3: 각 질문별로 {QUESTIONS_PER_ITEM}개씩 생성 요청...")
print(f"   서버: {SERVER_URL}")
print(f"   총 {len(questions)}개 질문 × {QUESTIONS_PER_ITEM}개 = {len(questions) * QUESTIONS_PER_ITEM}개 생성 예정")

all_results = []

for idx, original_question in enumerate(questions, 1):
    print(f"\n{'='*60}")
    print(f"📝 [{idx}/{len(questions)}] 원본 질문: {original_question}")
    print(f"{'='*60}")
    
    # 프롬프트 구성 - 원본 질문과의 연관성 강화
    prompt = f"""다음은 지원자의 이력서 요약입니다:

{resume_summary}

다음은 참고할 원본 면접 질문입니다:
"{original_question}"

**중요**: 위 원본 질문의 주제와 의도를 반드시 유지하면서, 이 지원자의 이력서 내용에 맞게 구체화한 질문을 {QUESTIONS_PER_ITEM}개 생성해주세요.

예시:
- 원본: "자기소개를 해보세요" → 생성: "보안 엔지니어로서의 경력과 KISA 인턴 경험을 중심으로 자기소개를 해주세요"
- 원본: "프로젝트 경험은?" → 생성: "Snort를 활용한 IDS 구축 프로젝트에서 어떤 역할을 맡으셨나요?"

**반드시 원본 질문의 핵심 주제를 유지하면서** 이력서의 구체적인 내용(프로젝트명, 기술명, 경험 등)을 포함해주세요.

형식:
1. [질문]
2. [질문]
3. [질문]

예상 질문:"""
    
    try:
        print(f"   📤 LLM에게 요청 전송 중...")
        response = requests.post(
            SERVER_URL,
            json={"message": prompt, "max_tokens": 300},
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result['response'].strip()
            
            print(f"   ✅ 생성 완료!")
            print(f"   응답: {generated_text[:100]}...")
            
            # 질문 파싱
            lines = generated_text.split('\n')
            parsed_questions = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    question = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- ')
                    if question:
                        parsed_questions.append(question)
            
            # 결과 저장
            for gen_q in parsed_questions:
                all_results.append({
                    '원본_질문': original_question,
                    '생성된_질문': gen_q,
                    '프롬프트_적용': 'No'
                })
            
            print(f"   📊 파싱된 질문 수: {len(parsed_questions)}개")
            
        else:
            print(f"   ❌ 서버 오류 (상태 코드: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # 서버 과부하 방지
    time.sleep(1)

# ========== 4. 결과 저장 ==========
print(f"\n💾 Step 4: 결과 저장 중...")
try:
    result_df = pd.DataFrame(all_results)
    
    # 엑셀 파일로 저장
    result_df.to_excel(OUTPUT_PATH, index=False)
    
    print(f"   ✅ 저장 완료!")
    print(f"   📁 파일: {OUTPUT_PATH}")
    print(f"   📊 총 생성된 질문 수: {len(all_results)}개")
    
except Exception as e:
    print(f"   ❌ 오류: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 기본 버전 완료!")
print("=" * 60)
