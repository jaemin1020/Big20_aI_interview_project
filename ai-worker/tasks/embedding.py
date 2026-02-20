import sys
import os
import json
import torch
from langchain_huggingface import HuggingFaceEmbeddings

# -----------------------------------------------------------
# [전역 설정] 
# nlpai-lab/KURE-v1: 한국어 문장 간의 의미적 유사성을 파악하는 데 특화된 모델입니다.
# -----------------------------------------------------------
EMBEDDING_MODEL = "nlpai-lab/KURE-v1" 

# [문법] _embedder = None
# 왜 필요할까? 모델은 용량이 매우 크기 때문에(수백 MB ~ GB), 함수를 호출할 때마다 
# 새로 로드하면 서버가 매우 느려지고 메모리가 금방 바닥납니다.
# 그래서 처음에만 로드하고 계속 재사용하기 위해 전역 변수로 선언해둡니다.
_embedder = None

def get_embedder(device):
    """
    [함수의 역할] 임베딩 모델을 메모리에 딱 한 번만 올리는 '관리자' 역할입니다. (싱글톤 패턴)
    [존재 이유] 모델 로딩은 '비싼 작업'입니다. 이 함수가 없다면 작업이 들어올 때마다 
               모델을 새로 다운로드하거나 읽어오느라 서비스가 마비될 수 있습니다.
    """
    global _embedder # 함수 밖의 전역 변수 _embedder를 수정하겠다는 선언입니다.
    
    if _embedder is None: # 아직 모델이 로드되지 않았을 때만 실행합니다.
        # [문법] 삼항 연산자: Docker 환경(/app)인지 로컬 환경인지에 따라 모델 저장 경로를 자동으로 결정합니다.
        cache_dir = "/app/models/embeddings" if os.path.exists("/app/models") else "./models/embeddings"
        
        # [문법] os.makedirs: 모델을 저장할 폴더가 없으면 에러가 나므로, 미리 폴더를 만들어둡니다.
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"🚀 [STEP5] 임베딩 모델 로드 시작 (모델: {EMBEDDING_MODEL})...")
        
        # [해석] HuggingFaceEmbeddings 객체를 생성합니다.
        # model_kwargs={'device': device}: GPU(cuda)를 쓸지 CPU를 쓸지 결정합니다.
        # encode_kwargs={'normalize_embeddings': True}: 벡터의 길이를 1로 맞추는 수학적 정규화입니다.
        # 이렇게 해야 나중에 '코사인 유사도'를 계산할 때 결과가 정확하게 나옵니다.
        _embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True},
            cache_folder=cache_dir
        )
        print("✅ 임베딩 모델 메모리 상주 완료!")
        
    return _embedder # 이미 로드된 상태라면 바로 기존 모델을 돌려줍니다.

def embed_chunks(chunks):
    """
    [함수의 역할] 잘게 쪼개진 텍스트 조각(Chunk)들을 수학적인 '벡터'로 변환합니다.
    [존재 이유] 인공지능은 텍스트를 직접 읽지 못합니다. 텍스트를 수백 개의 숫자 리스트(벡터)로 
               바꿔야만 수학적으로 '비슷한 의미'인지 계산할 수 있기 때문입니다.
    """
    # 1. 장치 설정: [문법] torch.cuda.is_available()는 내 컴퓨터에 쓸만한 그래픽카드가 있는지 체크합니다.
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # 2. 모델 일꾼 불러오기: 위에서 만든 get_embedder를 호출해 모델을 가져옵니다.
    embedder = get_embedder(device)

    # 3. 텍스트만 추출
    # [문법] 리스트 컴프리헨션: chunks 리스트 내부의 각 딕셔너리에서 "text" 키값만 뽑아 리스트를 만듭니다.
    # 예: [{"text": "안녕"}, {"text": "반가워"}] -> ["안녕", "반가워"]
    texts = [c["text"] for c in chunks]
    
    # 4. 벡터 변환 수행 (AI 연산)
    try:
        # [해석] embed_documents: 텍스트 리스트를 모델에 던져줍니다.
        # 결과값 vectors는 [[0.12, -0.5, ...], [0.8, 0.2, ...]] 같은 거대한 숫자 배열이 됩니다.
        vectors = embedder.embed_documents(texts)
    except Exception as e:
        # AI 모델 실행 중 에러(메모리 부족 등)가 나면 프로그램이 멈추지 않게 예외 처리를 합니다.
        print(f"❌ 임베딩 모델 실행 중 에러: {e}")
        return []

    # 5. 데이터와 벡터의 결합
    # [존재 이유] 나중에 DB에 저장할 때, "이 벡터가 어떤 텍스트에서 나왔는지" 알아야 하므로
    # 원본 텍스트와 메타데이터를 벡터와 한 세트로 묶어주는 과정입니다.
    embedded_result = []
    for i, c in enumerate(chunks): # [문법] i는 순번, c는 내용입니다.
        embedded_result.append({
            "text": c["text"],         # 검색 결과 화면에 보여줄 텍스트
            "type": c["type"],         # 이게 학력인지 경력인지 구분
            "metadata": c["metadata"], # 원본 파일 정보 등
            "vector": vectors[i]       # [핵심] AI가 계산한 수학적 좌표값
        })

    return embedded_result

# -----------------------------------------------------------
# [메인 실행부] if __name__ == "__main__":
# [존재 이유] 이 파일을 직접 실행했을 때만 테스트 코드가 돌아가게 합니다.
# 다른 파일에서 이 함수를 import해서 쓸 때는 테스트 코드가 실행되지 않아 안전합니다.
# -----------------------------------------------------------
if __name__ == "__main__":
    # 이전 단계(파싱, 청킹) 모듈들을 가져와서 전체 파이프라인이 잘 돌아가는지 확인합니다.
    # (실제 서비스에서는 이 부분이 아니라 Celery Task가 이 역할을 대신합니다.)
    pass