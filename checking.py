import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
# API 키가 환경변수에 없을 경우를 대비한 안전 장치 (실제로는 .env 필요)
openai_api_key = os.getenv("OPENAI_API_KEY")
upstage_api_key = os.getenv("UPSTAGE_API_KEY")

if not openai_api_key:
    print("⚠️ 경고: OPENAI_API_KEY가 환경변수에 설정되지 않았습니다.")
if not upstage_api_key:
    print("⚠️ 경고: UPSTAGE_API_KEY가 환경변수에 설정되지 않았습니다.")

openai_client = OpenAI(api_key=openai_api_key)
solar_client = OpenAI(api_key=upstage_api_key, base_url="https://api.upstage.ai/v1/solar")

# --- 정교화된 자기소개서 데이터 (각 변수에 할당) ---

# --- 신입 수준의 자기소개서 데이터 (각 변수에 할당) ---

r1_backend = """
백엔드 개발의 기초인 CRUD 기능을 안정적으로 구현하는 것에 집중하며, Python과 Django를 활용한 게시판 프로젝트를 진행했습니다.
처음에는 기능 구현에만 급급했으나, 데이터가 많아질 경우를 대비해 데이터베이스 인덱스를 설정해보며 쿼리 속도 차이를 체감했습니다.
RESTful한 API를 설계하기 위해 HTTP 메서드를 목적에 맞게 사용하려 노력했고,
특히 예외 처리 로직을 공통화하여 사용자에게 일관된 에러 메시지를 전달하는 구조를 설계한 경험이 있습니다.
기초가 탄탄하고 확장성 있는 코드를 작성하는 개발자가 되고 싶습니다.
"""

r2_frontend = """
사용자가 웹 서비스를 이용할 때 느끼는 편리함에 큰 매력을 느껴 프론트엔드 개발을 시작했습니다.
React를 공부하며 컴포넌트 기반 개발의 효율성을 익혔고, 프로젝트에서는 복잡해지는 상태 관리를 위해 Redux를 도입해보았습니다.
단순히 라이브러리를 사용하는 것에 그치지 않고, 왜 이 상태를 전역으로 관리해야 하는지 고민하며 구조를 짰습니다.
또한 다양한 화면 크기에서도 깨지지 않는 반응형 웹을 구현하기 위해 CSS-in-JS를 활용했으며,
API 통신 시 로딩 상태를 처리하여 사용자 경험(UX)을 개선하기 위해 노력했습니다.
"""

r3_devops = """
내 로컬 환경뿐만 아니라 실제 서버에서도 서비스가 안정적으로 돌아가는 과정에 관심이 많습니다.
단순한 수동 배포의 번거로움을 해결하기 위해 Docker를 공부하여 개발 환경을 컨테이너화했고,
AWS EC2 인스턴스에 직접 서비스를 올려본 경험이 있습니다. GitHub Actions를 활용해 코드가 push될 때마다
자동으로 빌드되고 테스트되는 CI 파이프라인을 구축하며 배포의 자동화 과정을 익혔습니다.
아직은 부족하지만 보안 그룹 설정이나 기본적인 네트워크 구조(VPC)를 이해하며 인프라 지식을 쌓아가고 있습니다.
"""

r4_collaboration = """
팀 프로젝트를 진행하며 소통과 협업의 즐거움을 알게 되었습니다.
다양한 팀원이 모여 개발하다 보니 발생하는 Git Conflict 문제를 해결하기 위해, 팀 내 브랜치 전략(Git Flow)을 제안하고
커밋 컨벤션을 정정하여 코드 관리를 효율화했습니다. 서로의 코드를 읽어보는 코드 리뷰 시간이
처음에는 어색했지만, 건설적인 피드백을 주고받으며 코드의 질이 높아지는 것을 경험했습니다.
함께 일하고 싶은 개발자가 되기 위해 문서화를 꼼꼼히 하고 지식을 공유하는 습관을 지니고 있습니다.
"""

r5_aiml = """
데이터가 가진 힘을 믿으며, Python 라이브러리를 활용해 문제를 해결하는 과정에 흥미를 느낍니다.
학부 시절 Pandas와 Scikit-learn을 사용해 영화 추천 시스템 프로젝트를 진행했습니다.
결측치 처리나 이상치 제거 같은 데이터 전처리 과정이 모델의 성능에 미치는 영향을 직접 확인했고,
단순 정확도(Accuracy)뿐만 아니라 정밀도(Precision)와 재현율(Recall)의 차이를 이해하며 모델을 평가했습니다.
최근에는 단순히 모델링에 그치지 않고, 학습된 모델을 API 형태로 서빙해보는 과정에 대해 공부하고 있습니다.
"""


resumes = [r1_backend, r2_frontend, r3_devops, r4_collaboration, r5_aiml]
labels = ["백엔드", "프론트", "데브옵스", "협업", "AI/ML"]

# --- 2. 질문 DB 정의 (신입 개발자 면접용 20문항) ---
questions = [
    # [백엔드 관련]
    "Q1: RESTful API의 특징과 장점은 무엇인가요?",
    "Q2: GET과 POST 요청의 차이점을 설명해 주세요.",
    "Q3: 데이터베이스에서 인덱스를 사용하는 이유와 주의할 점은 무엇인가요?",
    "Q4: 프로젝트 진행 중 발생한 서버 에러를 어떻게 디버깅하고 해결했나요?",

    # [프론트엔드 관련]
    "Q5: React의 Hook(useState, useEffect)을 사용하는 이유는 무엇인가요?",
    "Q6: 전역 상태 관리가 왜 필요한지 본인의 프로젝트 경험을 곁들여 설명해 주세요.",
    "Q7: 브라우저가 화면을 그리는 과정(렌더링)에 대해 아는 대로 설명해 주세요.",
    "Q8: 반응형 웹을 구현할 때 가장 중요하게 생각하는 요소는 무엇인가요?",

    # [인프라/데브옵스 관련]
    "Q9: Docker 컨테이너와 가상 머신(VM)의 근본적인 차이점은 무엇인가요?",
    "Q10: AWS EC2를 사용하며 보안 그룹(Security Group)을 어떻게 설정했나요?",
    "Q11: CI/CD 파이프라인을 구축하며 느낀 자동화 배포의 가장 큰 이점은?",
    "Q12: HTTP와 HTTPS의 차이점과 보안 전송이 중요한 이유를 설명해 주세요.",

    # [협업/인성 관련]
    "Q13: Git을 사용하며 충돌(Conflict)이 발생했을 때 어떻게 대처했나요?",
    "Q14: 본인이 생각하는 '좋은 코드'란 무엇이며, 이를 위해 어떤 노력을 하나요?",
    "Q15: 팀원과 의견이 다를 때 논리적으로 설득하거나 합의점을 찾는 본인만의 방식은?",
    "Q16: 개발 문서화(README 등)를 작성할 때 어떤 내용을 담으려 노력하나요?",

    # [데이터/AI 관련]
    "Q17: 데이터 전처리 과정이 모델의 성능에 미치는 영향에 대해 설명해 주세요.",
    "Q18: 모델의 과적합(Overfitting)이란 무엇이며, 이를 방지하기 위한 방법은?",
    "Q19: 프로젝트에서 사용한 모델 평가 지표와 그 지표를 선택한 이유는 무엇인가요?",
    "Q20: 머신러닝 프로젝트를 진행하며 겪은 가장 어려웠던 데이터 관련 문제는?"
]

# --- 3. 정답지 (각 자기소개서가 가져와야 할 질문 번호 매핑) ---
ground_truth = [
    [0, 1, 2, 3],    # 1. 백엔드
    [4, 5, 6, 7],    # 2. 프론트엔드
    [8, 9, 10, 11],  # 3. 데브옵스
    [12, 13, 14, 15],# 4. 협업
    [16, 17, 18, 19] # 5. AI/데이터
]

def get_embeddings(client, texts, model_name):
    try:
        response = client.embeddings.create(input=texts, model=model_name)
        return np.array([data.embedding for data in response.data])
    except Exception as e:
        print(f"❌ 임베딩 생성 실패 ({model_name}): {e}")
        # 오류 발생 시 빈 벡터 반환 또는 예외 전파
        return np.zeros((len(texts), 3072 if '3-large' in model_name else 4096))

# 2. 임베딩 및 유사도 계산
print("🚀 OpenAI 임베딩 생성 중...")
oe_res = get_embeddings(openai_client, resumes, "text-embedding-3-large")
oe_que = get_embeddings(openai_client, questions, "text-embedding-3-large")

print("🚀 Solar 임베딩 생성 중...")
sl_res = get_embeddings(solar_client, resumes, "solar-embedding-1-large-query")
sl_que = get_embeddings(solar_client, questions, "solar-embedding-1-large-passage")

print(f"\n{'='*120}")
print(f"{'자기소개 분야':<15} | {'순위':<4} | {'OpenAI (3072차원) 추천 리스트':<45} | {'Solar (4096차원) 추천 리스트'}")
print(f"{'='*120}")

for i, label in enumerate(labels):
    # 각 모델별 코사인 유사도 점수 산출
    try:
        oe_sims = cosine_similarity([oe_res[i]], oe_que)[0]
        sl_sims = cosine_similarity([sl_res[i]], sl_que)[0]

        # 상위 3개 인덱스 추출
        oe_top3 = np.argsort(oe_sims)[::-1][:3]
        sl_top3 = np.argsort(sl_sims)[::-1][:3]

        for rank in range(3):
            oe_idx = oe_top3[rank]
            sl_idx = sl_top3[rank]

            row_label = label if rank == 0 else ""
            # 질문 내용과 해당 점수 출력
            oe_text = f"{questions[oe_idx][:40]} ({oe_sims[oe_idx]:.3f})"
            sl_text = f"{questions[sl_idx][:40]} ({sl_sims[sl_idx]:.3f})"

            print(f"{row_label:<18} | {rank+1}위 | {oe_text:<48} | {sl_text}")
        print("-" * 120)
    except Exception as e:
        print(f"⚠️ 결과 집계 중 오류 발생 ({label}): {e}")