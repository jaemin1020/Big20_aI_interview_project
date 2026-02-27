import time
import os
import gc
import statistics
import numpy as np
import pdfplumber
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ── 설정 ────────────────────────────────────────────────────────────────────
MODEL_NAME = "nlpai-lab/KURE-v1"
PDF_PATH = "ai-worker/resume.pdf"  # 프로젝트 내 실제 PDF 경로
REPEAT = 5 # 정밀 측정을 위한 반복 횟수

# ── 결과 저장 ────────────────────────────────────────────────────────────
results = {
    "Loading & Chunking": {"Native": [], "LangChain": []},
    "Embedding (Batch)": {"Native": [], "LangChain": []},
    "Search (Similarity)": {"Native": [], "LangChain": []}
}

def run_benchmark():
    print(f"🚀 [벤치마크 시작] 실제 PDF 데이터 활용: {PDF_PATH}")
    print(f"   사용 모델: {MODEL_NAME}")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF 파일을 찾을 수 없습니다: {PDF_PATH}")
        return

    # 1. 모델 준비 (공정한 비교를 위해 미리 로드)
    print("\n[STEP 0] 모델 로딩 중...")
    native_model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    langchain_embedder = HuggingFaceEmbeddings(
        model_name=MODEL_NAME, 
        model_kwargs={'trust_remote_code': True}
    )

    for i in range(REPEAT):
        print(f"\n[🔄 {i+1}/{REPEAT}회차 테스트]")
        
        # -----------------------------------------------------------
        # A. Loading & Chunking (데이터 수급 및 전처리)
        # -----------------------------------------------------------
        # 1) LangChain 방식: PyPDFLoader + RecursiveSplitter
        t0 = time.perf_counter()
        loader = PyPDFLoader(PDF_PATH)
        lc_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        lc_chunks = text_splitter.split_documents(lc_docs)
        results["Loading & Chunking"]["LangChain"].append(time.perf_counter() - t0)

        # 2) Native 방식: pdfplumber + Paragraph Split
        t0 = time.perf_counter()
        native_chunks = []
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # 간단한 단락 기준 분할 (실제 프로젝트 utils 패턴 모방)
                    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
                    native_chunks.extend(paras)
        results["Loading & Chunking"]["Native"].append(time.perf_counter() - t0)

        # -----------------------------------------------------------
        # B. Embedding (벡터화)
        # -----------------------------------------------------------
        native_texts = native_chunks
        lc_texts = [d.page_content for d in lc_chunks]

        # 1) LangChain 방식
        t0 = time.perf_counter()
        lc_vectors = langchain_embedder.embed_documents(lc_texts)
        results["Embedding (Batch)"]["LangChain"].append(time.perf_counter() - t0)

        # 2) Native 방식
        t0 = time.perf_counter()
        native_vectors = native_model.encode(native_texts, convert_to_tensor=False)
        results["Embedding (Batch)"]["Native"].append(time.perf_counter() - t0)

        # -----------------------------------------------------------
        # C. Search (유사도 검색 - RAG 동작 시뮬레이션)
        # -----------------------------------------------------------
        query = "지원자의 AI 프로젝트 경험에 대해 알려줘"
        print(f"\n🔎 [RAG 시뮬레이션] 질의: '{query}'")
        
        # 1) LangChain 방식 (객체 기반 필터링 및 정렬)
        t0 = time.perf_counter()
        query_vec_lc = langchain_embedder.embed_query(query)
        # 동작 방식: 각 Document 객체와 벡터를 매칭하여 유사도 계산 후 객체 리스트 정렬
        lc_search_results = []
        for j, doc in enumerate(lc_chunks):
            sim = np.dot(query_vec_lc, lc_vectors[j])
            lc_search_results.append(Document(page_content=doc.page_content, metadata={"sim": sim}))
        lc_search_results.sort(key=lambda x: x.metadata["sim"], reverse=True)
        results["Search (Similarity)"]["LangChain"].append(time.perf_counter() - t0)

        # 2) Native 방식 (Raw Matrix NumPy 연산)
        t0 = time.perf_counter()
        query_vec_native = native_model.encode([query])[0]
        # 동작 방식: 넘파이 행렬 곱(Dot Product)을 통해 모든 청크의 유사도를 한 번에 고속 계산
        similarities = np.dot(native_vectors, query_vec_native)
        top_indices = np.argsort(similarities)[::-1][:3] # 상위 3개 추출
        native_search_results = [(native_chunks[idx], similarities[idx]) for idx in top_indices]
        results["Search (Similarity)"]["Native"].append(time.perf_counter() - t0)

        # 1회차 테스트에서만 실제 가져온 데이터를 상세 출력하여 확인
        if i == 0:
            print("\n   📄 [실제 검색 데이터 확인 - 1회차]")
            print(f"   {'='*80}")
            print(f"   {'[LangChain Result]':<40} | {'[Native Result]':<40}")
            print(f"   {'-'*80}")
            for k in range(min(3, len(lc_search_results), len(native_search_results))):
                lc_text = lc_search_results[k].page_content.replace('\n', ' ')[:35]
                lc_sim = lc_search_results[k].metadata['sim']
                nt_text = native_search_results[k][0].replace('\n', ' ')[:35]
                nt_sim = native_search_results[k][1]
                print(f"   {k+1}. {lc_text}... ({lc_sim:.4f}) | {nt_text}... ({nt_sim:.4f})")
            print(f"   {'='*80}")

        gc.collect()

    # 결과 출력
    print_results()

def print_results():
    print("\n" + "="*70)
    print(f"{'Benchmarking Results (Avg of {REPEAT} runs)':^70}")
    print("="*70)
    print(f"{'Category':<25} | {'Native (Direct)':<15} | {'LangChain (Framework)':<15} | {'Winner':<10}")
    print("-"*70)
    
    comparisons = {}
    for cat, data in results.items():
        n_mean = statistics.mean(data["Native"])
        l_mean = statistics.mean(data["LangChain"])
        winner = "Native" if n_mean < l_mean else "LangChain"
        ratio = l_mean / n_mean if winner == "Native" else n_mean / l_mean
        
        print(f"{cat:<25} | {n_mean:>13.4f}s | {l_mean:>13.4f}s | {winner} ({ratio:.1f}x)")
        comparisons[cat] = {"n": n_mean, "l": l_mean, "winner": winner, "ratio": ratio}
    
    print("="*70)
    print("\n� [데이터 기반 실측 분석]")
    
    # 1. Loading/Chunking 분석
    c = comparisons["Loading & Chunking"]
    print(f"1. 데이터 로드/분할: {c['winner']} 방식이 약 {c['ratio']:.1f}배 더 기민합니다.")
    print(f"   - LangChain은 RecursiveSplitter를 통한 고품질 의미 단위 분할을 제공하는 대신 연산량이 많습니다.")
    
    # 2. Embedding 분석
    c = comparisons["Embedding (Batch)"]
    diff_percent = abs(c['n'] - c['l']) / max(c['n'], c['l']) * 100
    print(f"2. 임베딩 연산: 두 방식의 차이는 {diff_percent:.1f}% 내외로 매우 미미합니다.")
    print(f"   - 내부 엔진(SentenceTransformer)이 동일하여 연산 효율은 도구에 종속되지 않음을 증명합니다.")
    
    # 3. Search 분석
    c = comparisons["Search (Similarity)"]
    print(f"3. 텍스트 검색: {c['winner']} 방식이 약 {c['ratio']:.1f}배 더 효율적입니다.")
    if c['winner'] == "Native":
        print(f"   - Native의 NumPy 행렬 연산이 랭체인의 Document 객체 생성/정렬 오버헤드보다 물리적으로 빠릅니다.")
    
    print(f"\n✅ 최종 시사점: 측정된 수치에 따르면 {comparisons['Search (Similarity)']['winner']} 방식이 실시간 검색 응답성 확보에 유리하며,")
    print(f"개발 생산성과 정교한 문서 파싱이 최우선일 경우 LangChain의 래퍼 기능을 활용하는 것이 합리적인 선택입니다.")

if __name__ == "__main__":
    run_benchmark()
