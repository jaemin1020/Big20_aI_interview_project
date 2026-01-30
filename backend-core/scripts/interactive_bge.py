import sys
import os
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select, text
import numpy as np

# 경로 설정
sys.path.append('/app')
from database import engine
from models import Question

def interactive_mode():
    print('\n��� BGE-M3 대화형 모드 시작! (종료: quit 입력)')
    print('�� 모델 로딩 중 (잠시만 기다려주세요)...')
    try:
        model = SentenceTransformer('BAAI/bge-m3')
    except Exception as e:
        print(f'❌ 모델 로드 실패: {e}')
        return

    print('✅ 모델 준비 완료! 궁금한 내용을 입력하면 유사한 검증된 질문을 찾아줍니다.')
    
    while True:
        try:
            user_input = input('\n��� 입력 (이력서 내용이나 키워드): ')
            if user_input.lower() in ['quit', 'exit', 'q']:
                print('��� 종료합니다.')
                break
                
            if len(user_input.strip()) < 2:
                continue
                
            # 1. 임베딩 생성
            query_vec = model.encode(user_input, normalize_embeddings=True).tolist()
            
            # 2. DB 검색
            with Session(engine) as session:
                # 코사인 유사도 검색 (1 - 거리)
                stmt = select(
                    Question,
                    text(f"1 - (embedding <=> '{query_vec}') AS similarity")
                ).where(
                    Question.embedding.isnot(None)
                ).order_by(text('similarity DESC')).limit(3)
                
                results = session.exec(stmt).all()
                
                if not results:
                    print('⚠️ 데이터베이스에 질문이 없거나 검색되지 않았습니다.')
                    continue

                print(f'\n��� 검색 결과 Top 3:')
                for i, (q, sim) in enumerate(results, 1):
                    sim_score = float(sim)
                    print(f'{i}. [유사도: {sim_score:.4f}] {q.content}')
                    print(f'   - 카테고리: {q.category.value if hasattr(q.category, "value") else q.category}, 난이도: {q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty}')
        except KeyboardInterrupt:
            print('\n��� 종료합니다.')
            break
        except Exception as e:
            print(f'⚠️ 오류 발생: {e}')

if __name__ == '__main__':
    interactive_mode()
