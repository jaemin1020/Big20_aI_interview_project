"""
VectorDB 연결 및 기본 동작 테스트
- DB 연결 확인
- pgvector 확장 확인
- 샘플 임베딩 저장/검색 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, text
from database import engine, init_db

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 60)
    print("1️⃣ 데이터베이스 연결 테스트")
    print("=" * 60)

    try:
        with Session(engine) as session:
            result = session.exec(text("SELECT 1")).first()
            print("✅ 데이터베이스 연결 성공!")
            return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {str(e)}")
        return False

def test_pgvector_extension():
    """pgvector 확장 설치 확인"""
    print("\n" + "=" * 60)
    print("2️⃣ pgvector 확장 확인")
    print("=" * 60)

    try:
        with Session(engine) as session:
            # pgvector 확장 확인
            result = session.exec(
                text("SELECT * FROM pg_extension WHERE extname = 'vector'")
            ).first()

            if result:
                print("✅ pgvector 확장이 설치되어 있습니다!")
                print(f"   버전: {result[1]}")
                return True
            else:
                print("❌ pgvector 확장이 설치되어 있지 않습니다.")
                print("   다음 명령어로 설치하세요:")
                print("   CREATE EXTENSION vector;")
                return False
    except Exception as e:
        print(f"❌ 확장 확인 실패: {str(e)}")
        return False

def test_vector_operations():
    """벡터 연산 테스트"""
    print("\n" + "=" * 60)
    print("3️⃣ 벡터 연산 테스트")
    print("=" * 60)

    try:
        with Session(engine) as session:
            # 샘플 벡터 생성
            vec1 = [0.1, 0.2, 0.3]
            vec2 = [0.15, 0.25, 0.35]

            # 코사인 거리 계산
            result = session.exec(
                text(f"SELECT '{vec1}' <=> '{vec2}' AS distance")
            ).first()

            print(f"✅ 벡터 연산 성공!")
            print(f"   벡터1: {vec1}")
            print(f"   벡터2: {vec2}")
            print(f"   코사인 거리: {result[0]:.6f}")
            print(f"   코사인 유사도: {1 - result[0]:.6f}")
            return True
    except Exception as e:
        print(f"❌ 벡터 연산 실패: {str(e)}")
        return False

def test_tables_exist():
    """테이블 존재 확인"""
    print("\n" + "=" * 60)
    print("4️⃣ 테이블 존재 확인")
    print("=" * 60)

    tables = [
        'users',
        'job_postings',
        'interviews',
        'questions',
        'transcripts',
        'evaluation_reports',
        'answer_bank'
    ]

    try:
        with Session(engine) as session:
            for table in tables:
                result = session.exec(
                    text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = '{table}'
                        )
                    """)
                ).first()

                if result[0]:
                    # 행 개수 확인
                    count = session.exec(text(f"SELECT COUNT(*) FROM {table}")).first()[0]
                    print(f"✅ {table:20s} - {count:4d} rows")
                else:
                    print(f"❌ {table:20s} - 존재하지 않음")

        return True
    except Exception as e:
        print(f"❌ 테이블 확인 실패: {str(e)}")
        return False

def test_embedding_model():
    """임베딩 모델 로드 테스트"""
    print("\n" + "=" * 60)
    print("5️⃣ 임베딩 모델 로드 테스트")
    print("=" * 60)

    try:
        from sentence_transformers import SentenceTransformer

        print("🔄 모델 다운로드 중... (최초 1회만 시간 소요)")
        model = SentenceTransformer('jhgan/ko-sroberta-multitask')

        # 테스트 임베딩 생성
        test_text = "Python 개발자 면접 질문"
        embedding = model.encode(test_text)

        print(f"✅ 임베딩 모델 로드 성공!")
        print(f"   모델: jhgan/ko-sroberta-multitask")
        print(f"   임베딩 차원: {len(embedding)}")
        print(f"   테스트 텍스트: '{test_text}'")
        print(f"   임베딩 샘플: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")

        return True
    except Exception as e:
        print(f"❌ 임베딩 모델 로드 실패: {str(e)}")
        print("\n해결 방법:")
        print("1. 인터넷 연결 확인")
        print("2. HuggingFace 모델 수동 다운로드:")
        print("   python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')\"")
        return False

def test_vector_search():
    """벡터 검색 테스트 (데이터가 있을 경우)"""
    print("\n" + "=" * 60)
    print("6️⃣ 벡터 검색 테스트")
    print("=" * 60)

    try:
        with Session(engine) as session:
            # questions 테이블에 데이터가 있는지 확인
            count = session.exec(text("SELECT COUNT(*) FROM questions WHERE embedding IS NOT NULL")).first()[0]

            if count == 0:
                print("⚠️ 검색할 질문 데이터가 없습니다.")
                print("   다음 명령어로 샘플 데이터를 삽입하세요:")
                print("   python scripts/populate_vectordb.py")
                return False

            print(f"✅ {count}개의 질문 데이터 발견!")

            # 샘플 검색
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('jhgan/ko-sroberta-multitask')

            query = "파이썬 멀티스레딩"
            query_embedding = model.encode(query).tolist()

            results = session.exec(
                text(f"""
                    SELECT
                        id,
                        content,
                        category,
                        difficulty,
                        embedding <=> '{query_embedding}' AS distance
                    FROM questions
                    ORDER BY distance
                    LIMIT 3
                """)
            ).all()

            print(f"\n🔍 검색 쿼리: '{query}'")
            print(f"📊 검색 결과 (상위 3개):\n")

            for i, row in enumerate(results, 1):
                similarity = 1 - row[4]
                print(f"{i}. [유사도: {similarity:.4f}] [{row[3]}]")
                print(f"   {row[1][:100]}...")
                print()

            return True

    except Exception as e:
        print(f"❌ 벡터 검색 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "🧪 VectorDB 시스템 테스트 시작\n")

    results = []

    # 1. DB 연결
    results.append(("데이터베이스 연결", test_database_connection()))

    # 2. pgvector 확장
    results.append(("pgvector 확장", test_pgvector_extension()))

    # 3. 벡터 연산
    results.append(("벡터 연산", test_vector_operations()))

    # 4. 테이블 존재
    init_db()  # 테이블 생성
    results.append(("테이블 생성", test_tables_exist()))

    # 5. 임베딩 모델
    results.append(("임베딩 모델", test_embedding_model()))

    # 6. 벡터 검색
    results.append(("벡터 검색", test_vector_search()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{status:10s} - {name}")

    success_count = sum(1 for _, r in results if r)
    total_count = len(results)

    print(f"\n총 {total_count}개 테스트 중 {success_count}개 성공 ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("\n🎉 모든 테스트 통과! VectorDB가 정상적으로 작동합니다.")
        print("\n다음 단계:")
        print("1. python scripts/populate_vectordb.py - 샘플 데이터 삽입")
        print("2. python scripts/vector_utils.py - 검색 기능 테스트")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 위의 오류 메시지를 확인하세요.")

if __name__ == "__main__":
    run_all_tests()
