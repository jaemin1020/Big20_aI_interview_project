import sys
import os
import json
import torch

# 🚨 [최신 표준] langchain_huggingface 패키지 사용 (v0.2+)
from langchain_huggingface import HuggingFaceEmbeddings

# -----------------------------------------------------------
# [모델 설정]
# 사용자가 선택한 최신 한국어 임베딩 모델
# -----------------------------------------------------------
EMBEDDING_MODEL = "nlpai-lab/KURE-v1" 

# 2. 임베딩 모델 싱글톤 관리
_embedder = None

def get_embedder(device):
    global _embedder
    if _embedder is None:
        cache_dir = "/app/models/embeddings" if os.path.exists("/app/models") else "./models/embeddings"
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"🚀 [STEP5] 임베딩 모델 상주 작업 시작 (모델: {EMBEDDING_MODEL})...")
        print(f"📂 캐시 경로: {cache_dir} (첫 실행 시 다운로드로 인해 3~5분 소요될 수 있습니다)")
        
        _embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True},
            cache_folder=cache_dir
        )
        print("✅ 임베딩 모델 메모리 상주 완료!")
    return _embedder

def embed_chunks(chunks):
    # 1. 장치 설정 (GPU 우선)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # 2. 임베딩 모델 가져오기 (이미 로드되어 있으면 즉시 반환)
    print(f"📡 [STEP5] 모델 상태 확인 중...")
    embedder = get_embedder(device)
    print(f"👉 사용 장치: {device} (Warm Start 적용짐)")

    # 3. 텍스트 추출
    texts = [c["text"] for c in chunks]
    
    # 4. 벡터 변환 수행
    try:
        # embed_documents: 여러 문장을 한 번에 벡터화
        vectors = embedder.embed_documents(texts)
    except Exception as e:
        print(f"❌ 임베딩 모델 실행 중 에러: {e}")
        return []

    # 5. 결과 합치기 (메타데이터 + 벡터)
    embedded_result = []
    for i, c in enumerate(chunks):
        embedded_result.append({
            "text": c["text"],         # 청크 텍스트
            "type": c["type"],         # 데이터 타입 (header, education 등)
            "metadata": c["metadata"], # 원본 출처 정보
            "vector": vectors[i]       # [핵심] 768 or 1024차원 벡터
        })

    print(f"[STEP5] 임베딩 완료! (총 {len(vectors)}개 청크)")
    
    # [중요] 벡터 차원 확인 (DB 테이블 생성 시 이 숫자가 필요함)
    if vectors:
        print(f"👉 벡터 차원(Dimension): {len(vectors[0])}")
    
    return embedded_result

# -----------------------------------------------------------
# 테스트 실행 코드
# -----------------------------------------------------------
if __name__ == "__main__":
    # 이전 단계 모듈 import
    try:
        from parse_resume import parse_resume_final 
        from chunking import chunk_resume
    except ImportError as e:
        print(f"❌ 모듈 Import 실패: {e}")
        sys.exit(1)

    # 1. 파일 경로 확인
    target_pdf = "resume.pdf"
    if not os.path.exists(target_pdf):
        target_pdf = "/app/resume.pdf"

    if os.path.exists(target_pdf):
        print(f"🚀 [Pipeline] 파일 로드: {target_pdf}")
        
        # Step 2: 파싱
        parsed_data = parse_resume_final(target_pdf)
        
        if parsed_data:
            # Step 4: 청킹
            chunks = chunk_resume(parsed_data)
            
            if chunks:
                # Step 5: 임베딩
                embedded_data = embed_chunks(chunks)
                
                if embedded_data:
                    # 결과 저장
                    output_file = "embedded_result.json"
                    
                    # 미리보기 (벡터는 너무 기니까 길이만 출력)
                    print("\n--- [임베딩 결과 예시 (첫 번째 청크)] ---")
                    sample = embedded_data[0].copy()
                    vec_len = len(sample['vector'])
                    sample["vector"] = f"[Vector of size {vec_len}...]" 
                    print(json.dumps(sample, indent=2, ensure_ascii=False))

                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(embedded_data, f, indent=2, ensure_ascii=False)
                    print(f"\n✅ 저장 완료: {output_file}")
            else:
                print("❌ 청킹된 데이터가 없습니다.")
        else:
            print("❌ 파싱 실패")
    else:
        print(f"❌ 파일이 없습니다: {target_pdf}")
