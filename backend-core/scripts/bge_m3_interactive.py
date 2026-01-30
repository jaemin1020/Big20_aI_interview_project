import sys
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import time

# 스크립트 위치의 부모 디렉토리를 경로에 추가하여 모듈 임포트 가능하게 함 (필요시)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 60)
    print("🤖 BGE-M3 대화형 테스트 (Interactive Test)")
    print("=" * 60)
    print("이 스크립트는 프로젝트 데이터를 변경하지 않고 모델만 테스트합니다.")
    print("-" * 60)

def load_model():
    print("\n🔄 모델을 로드하고 있습니다... (잠시만 기다려주세요)")
    try:
        model = SentenceTransformer('BAAI/bge-m3')
        print("✅ 모델 로드 완료!")
        return model
    except Exception as e:
        print(f"\n❌ 모델 로드 실패: {e}")
        sys.exit(1)

def mode_similarity(model):
    print("\n📝 [모드 1] 두 문장 간의 유사도 비교")
    print("비교할 두 문장을 입력하세요. (종료하려면 'q' 입력)")

    while True:
        print("\n" + "-" * 40)
        text1 = input("문장 1: ").strip()
        if text1.lower() == 'q': break
        if not text1: continue

        text2 = input("문장 2: ").strip()
        if text2.lower() == 'q': break
        if not text2: continue

        # 임베딩 생성
        embeddings = model.encode([text1, text2], normalize_embeddings=True)

        # 코사인 유사도 계산 (내적)
        similarity = np.dot(embeddings[0], embeddings[1])

        print(f"\n📊 유사도 점수: {similarity:.4f}")

        if similarity > 0.8:
            print("=> 매우 유사함 (Very Similar)")
        elif similarity > 0.6:
            print("=> 꽤 유사함 (Similar)")
        elif similarity > 0.4:
            print("=> 약간 관련있음 (Somewhat Related)")
        else:
            print("=> 관련 없음 (Not Related)")

def mode_search(model):
    print("\n🔎 [모드 2] 문서 검색 테스트")
    print("검색 대상이 될 문서들을 먼저 설정합니다.")

    # 기본 문서셋
    documents = [
        "Python은 간결하고 읽기 쉬운 문법을 가진 프로그래밍 언어입니다.",
        "Java는 객체 지향 프로그래밍 언어로 안정성이 높습니다.",
        "Docker는 애플리케이션을 컨테이너화하여 배포하는 도구입니다.",
        "React는 효율적인 사용자 인터페이스를 위한 JavaScript 라이브러리입니다.",
        "SQL은 관계형 데이터베이스 관리 시스템에서 데이터를 관리하기 위한 언어입니다.",
        "머신러닝은 데이터를 통해 컴퓨터가 학습하게 하는 인공지능의 한 분야입니다.",
        "CI/CD는 지속적 통합 및 지속적 배포를 의미하며 개발 파이프라인을 자동화합니다."
    ]

    print(f"\n기본 문서 ({len(documents)}개)가 로드되었습니다.")
    print("추가할 문서가 있다면 입력하세요. (완료하려면 엔터, 초기화하려면 'cls')")

    while True:
        doc = input("추가 문서 > ").strip()
        if doc == 'cls':
            documents = []
            print("문서 목록이 초기화되었습니다.")
            continue
        if not doc:
            break
        documents.append(doc)
        print(f"문서 추가됨. (총 {len(documents)}개)")

    if not documents:
        print("검색할 문서가 없습니다. 메인 메뉴로 돌아갑니다.")
        return

    print("\n🔄 문서 임베딩 생성 중...")
    doc_embeddings = model.encode(documents, normalize_embeddings=True)
    print("✅ 준비 완료! 검색어를 입력하세요. (종료하려면 'q')")

    while True:
        query = input("\n검색어 > ").strip()
        if query.lower() == 'q': break
        if not query: continue

        query_emb = model.encode([query], normalize_embeddings=True)[0]

        # 유사도 계산
        similarities = np.dot(doc_embeddings, query_emb)

        # 상위 3개 추출
        top_k = min(3, len(documents))
        top_indices = np.argsort(similarities)[::-1][:top_k]

        print(f"\n🔍 '{query}' 검색 결과:")
        for rank, idx in enumerate(top_indices, 1):
            score = similarities[idx]
            print(f"  {rank}. [{score:.4f}] {documents[idx]}")

def main():
    clear_screen()
    print_header()

    model = load_model()

    while True:
        print("\n" + "=" * 60)
        print("선택할 작업을 입력하세요:")
        print("1. 문장 유사도 비교 (Similarity Check)")
        print("2. 문서 검색 테스트 (Search Test)")
        print("q. 종료 (Quit)")

        choice = input("\n선택 > ").strip().lower()

        if choice == '1':
            mode_similarity(model)
        elif choice == '2':
            mode_search(model)
        elif choice == 'q':
            print("\n👋 프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")

if __name__ == "__main__":
    main()
