import logging
import os
import sys
import time

# ai-worker 및 backend-core 경로 추가
app_root = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(app_root, "..", "backend-core"))
sys.path.insert(0, backend_root)
sys.path.insert(0, app_root)

from sqlmodel import Session, select, func
from db import engine
from db_models import Question
from utils.vector_utils import get_embedding_generator

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("BatchEmbed")

def batch_embed_questions(batch_size: int = 128):
    generator = get_embedding_generator()
    
    with Session(engine) as session:
        # 질문 총 개수 확인 (임베딩이 없는 것만)
        total_stmt = select(func.count(Question.id)).where(Question.embedding == None)
        total_to_process = session.exec(total_stmt).one()
        
        if total_to_process == 0:
            logger.info("모든 질문에 이미 임베딩이 존재합니다.")
            return

        logger.info(f"총 {total_to_process}개의 질문에 대한 임베딩 생성을 시작합니다. (배치 크기: {batch_size})")

        processed = 0
        start_time = time.time()

        while True:
            # 배치 단위로 질문 가져오기
            stmt = select(Question).where(Question.embedding == None).limit(batch_size)
            questions = session.exec(stmt).all()
            
            if not questions:
                break
            
            # 텍스트 추출 및 벡터화
            texts = [q.content for q in questions]
            embeddings = generator.encode_batch(texts, is_query=True)
            
            # DB 업데이트
            for q, emb in zip(questions, embeddings):
                q.embedding = emb
                session.add(q)
            
            session.commit()
            processed += len(questions)
            
            elapsed = time.time() - start_time
            avg_time = elapsed / processed
            remaining_time = (total_to_process - processed) * avg_time
            
            logger.info(f"진행률: {processed}/{total_to_process} ({processed/total_to_process*100:.2f}%) - "
                        f"남은 예상 시간: {remaining_time/60:.2f}분")

    logger.info(f"✅ 총 {processed}개의 질문 임베딩 생성 완료!")

if __name__ == "__main__":
    batch_embed_questions()
