import sys
import os
import time
import gc 
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager
from langchain_core.prompts import PromptTemplate

# -----------------------------------------------------------
# [모델 경로 설정]
# -----------------------------------------------------------
local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
docker_path = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

if os.path.exists(local_path):
    model_path = local_path
elif os.path.exists(docker_path):
    model_path = docker_path
else:
    print(f"❌ 모델 파일을 찾을 수 없습니다.")
    sys.exit(1)

 # -----------------------------------------------------------
# [프롬프트 수정] ★ 여기가 원인입니다! 아래 내용으로 교체하세요.
# -----------------------------------------------------------
PROMPT_TEMPLATE = """[|system|]
너는 15년 차 베테랑 '보안 직무 면접관'이다. 
지금은 **면접이 한창 진행 중인 상황**이다. (자기소개는 이미 끝났다.)
제공된 [이력서 내용]을 근거로, 해당 단계({stage})에 맞는 **날카로운 질문 1개**만 던져라.

[작성 절대 금지 사항] 
1. **"자기소개 부탁드립니다" 절대 금지.** (이미 했다고 가정)
2. **"(잠시 침묵)", "답변 감사합니다"** 같은 가상의 지문이나 대본을 쓰지 마라.
3. 질문 앞뒤에 사족을 붙이지 말고 **질문만 깔끔하게** 출력하라.

[질문 스타일 가이드]
1. 시작은 반드시 **"{name}님,"** 으로 부르며 시작할 것.
2. **"이력서를 보니...", "자소서를 읽어보니 ~라고 하셨는데..."** 처럼 근거를 명확히 댈 것.
3. 말투는 정중하면서도 예리한 면접관 톤(..하셨는데, ..설명해 주시겠습니까?)을 유지할 것.
[|endofturn|]
[|user|]
# 평가 단계: {stage}
# 평가 의도: {guide}
# 지원자 이력서 근거:
{context}

# 요청:
위 내용을 바탕으로 {name} 지원자에게 **단도직입적으로** 질문을 던져줘.
[|endofturn|]
[|assistant|]
"""

def generate_human_like_question(llm, name, stage, guide, context_list):
    if not context_list:
        return "❌ (관련 이력서 내용을 찾지 못해 질문을 생성할 수 없습니다)"

    texts = [item['text'] for item in context_list] if isinstance(context_list[0], dict) else context_list
    context_text = "\n".join([f"- {txt}" for txt in texts])
    
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm
    
    try:
        result = chain.invoke({
            "name": name,
            "stage": stage,
            "guide": guide,
            "context": context_text
        })
        return str(result).strip()
    except Exception as e:
        return f"에러 발생: {e}"

# -----------------------------------------------------------
# [메인 실행 함수]
# -----------------------------------------------------------
def main():
    # 1. LLM 초기화
    callback_manager = CallbackManager([])
    
    print(f"Loading Model: {model_path} ...")
    llm = LlamaCpp(
        model_path=model_path,
        temperature=0.4,
        n_ctx=4096,
        max_tokens=512,
        n_gpu_layers=-1,
        verbose=False,
        stop=["[|endofturn|]", "[|assistant|]"]
    )

    # 2. Step 7 모듈 로드
    try:
        # ★ 주의: 이전에 드린 '하이브리드 검색'이 적용된 step7_retrieve.py 여야 합니다!
        from step7_rag_retrieval import retrieve_context 
    except ImportError:
        print("❌ step7_rag_retrieval.py 모듈을 찾을 수 없습니다.")
        return

    # 3. 지원자 정보 및 시나리오
    candidate_name = "최승우"
    resume_id = 1

    generic_interview_plan = [
        {
            "stage": "1. 직무 지식 평가",
            "search_query": "보안 기술 스킬 도구 활용 능력",
            "filter_category": "certification",  # 자격증/스킬에서 찾기
            "guide": "지원자가 사용한 기술(Tool, Language)의 구체적인 설정법이나, 기술적 원리(Deep Dive)를 물어볼 것."
        },
        {
            "stage": "2. 직무 경험 평가",
            "search_query": "프로젝트 성과 달성 경험 결과",
            "filter_category": "project",       # 프로젝트에서만 찾기 (중요!)
            "guide": "프로젝트에서 달성한 수치적 성과(%)의 결정적 요인이 무엇인지, 구체적으로 어떤 데이터를 다뤘는지 물어볼 것."
        },
        {
            "stage": "3. 문제 해결 능력 평가",
            "search_query": "문제 해결 기술적 난관 극복",
            # 필터 없으면 전체에서 찾음 (None)
            "guide": "지원자가 직면한 한계점이나 문제 상황을 어떻게 정의했고, 어떤 논리적 사고 과정을 통해 해결책을 도출했는지 물어볼 것."
        },
        {
            "stage": "4. 의사소통 및 협업 평가",
            "search_query": "협업 갈등 해결 설득",
            "filter_category": "narrative",     # 자소서에서 찾기
            "guide": "팀원과의 의견 대립 상황에서 본인의 주장을 관철시키기 위해 어떤 객관적 근거를 사용했는지 대화 과정을 물어볼 것."
        },
               {

            "stage": "5. 책임감 및 가치관 평가",

            "search_query": "직업 윤리 목표 가치관",  

            "filter_category": "narrative",     # RAG가 '가치관' 관련 내용을 찾아옴

            "guide": "이상적인 목표(완벽함)와 현실적인 제약(효율성, 오탐 등) 사이에서 어떻게 균형을 맞출 것인지 물어볼 것."

        },
        {

            "stage": "6. 변화 수용력 및 성장의지 평가",

            "search_query": "성장 계획 자기계발 미래",

            "filter_category": "narrative",        # RAG가 '미래 계획' 관련 내용을 찾아옴

            "guide": "현재 기술 트렌드 변화에 맞춰 구체적으로 어떤 학습을 하고 있으며, 이를 실무에 어떻게 적용할 계획인지 물어볼 것."

        }



        # ... 필요시 추가 ...
    ]

    print(f"\n🚀 [AI 면접관 ({candidate_name} 지원자) 면접 시작]")
    print("=" * 60)

    for step in generic_interview_plan:
        print(f"\n📌 {step['stage']}")
        
        # ------------------------------------------------------------------
        # ★ [수정됨] filter_category 값을 함수에 전달하는 부분!
        # ------------------------------------------------------------------
        contexts = retrieve_context(
            step['search_query'], 
            resume_id=resume_id, 
            top_k=2,
            filter_category=step.get('filter_category') # 👈 여기가 핵심입니다!
        )
        
        if contexts:
            # 미리보기 출력
            preview = contexts[0]['text'].replace("\n", " ")[:60]
            # (디버깅용) 어떤 카테고리가 걸렸는지 확인
            meta_info = contexts[0].get('meta', {})
            print(f"   📄 [근거 데이터({meta_info.get('category', 'N/A')})]: {preview}...")
        else:
            print("   ❌ (관련 내용을 찾지 못함)")
            continue

        # 질문 생성
        question = generate_human_like_question(
            llm=llm,
            name=candidate_name,
            stage=step['stage'],
            guide=step['guide'],
            context_list=contexts
        )
        
        print(f"\n🎤 [AI 면접관의 질문]")
        print("-" * 60)
        print(question)
        print("-" * 60)
        
        time.sleep(2)

    # 4. 종료
    print("\n✅ 면접 종료. 리소스를 정리합니다...")
    del llm
    gc.collect()

if __name__ == "__main__":
    main()