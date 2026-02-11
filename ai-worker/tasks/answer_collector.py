"""
우수 답변 자동 수집 및 벡터화
평가 점수가 높은 답변을 AnswerBank에 저장
"""
import logging
from celery import shared_task
from sqlmodel import Session
from db import engine
from db import AnswerBank, Transcript, Question

# 벡터 생성 유틸
import sys
sys.path.append('/app/utils')
from vector_utils import generate_answer_embedding

logger = logging.getLogger("AI-Worker-AnswerCollector")

# 우수 답변 기준 점수
EXCELLENT_THRESHOLD = 85.0

@shared_task(name="tasks.answer_collector.collect_excellent_answer")
def collect_excellent_answer(transcript_id: int, evaluation_score: float):
    """
    평가 점수가 높은 답변을 AnswerBank에 자동 저장
    
    Args:
        transcript_id: 답변이 저장된 Transcript ID
        evaluation_score: 평가 점수 (0-100)
    
    Returns:
        dict: 수집 결과
    
    Raises:
        ValueError: 평가 점수가 기준 이하인 경우

    생성자: ejm
    생성일자: 2026-02-04
    """
    # 점수 체크
    if evaluation_score < EXCELLENT_THRESHOLD:
        logger.debug(f"Score {evaluation_score} below threshold {EXCELLENT_THRESHOLD}, skipping")
        return {"status": "skipped", "reason": "score_too_low"}
    
    try:
        with Session(engine) as session:
            # 1. Transcript 조회
            transcript = session.get(Transcript, transcript_id)
            if not transcript:
                logger.error(f"Transcript {transcript_id} not found")
                return {"status": "error", "reason": "transcript_not_found"}
            
            # 사용자 답변만 수집
            if transcript.speaker != "User":
                return {"status": "skipped", "reason": "not_user_answer"}
            
            # 2. 질문 조회
            if not transcript.question_id:
                logger.warning(f"Transcript {transcript_id} has no question_id")
                return {"status": "skipped", "reason": "no_question"}
            
            question = session.get(Question, transcript.question_id)
            if not question:
                logger.error(f"Question {transcript.question_id} not found")
                return {"status": "error", "reason": "question_not_found"}
            
            # 3. 벡터 생성
            logger.info(f"Generating embedding for answer: {transcript.text[:50]}...")
            embedding = generate_answer_embedding(transcript.text)
            
            # 4. 중복 체크 (벡터 유사도 기반) - TODO 해결
            from sqlmodel import select
            stmt = select(AnswerBank).where(
                AnswerBank.question_id == question.id
            )
            existing_answers = session.exec(stmt).all()
            
            # 유사도 임계값 (0.95 이상이면 중복으로 간주)
            SIMILARITY_THRESHOLD = 0.95
            
            for existing in existing_answers:
                if existing.embedding:
                    # 코사인 유사도 계산 (간단한 방법)
                    import numpy as np
                    emb1 = np.array(embedding)
                    emb2 = np.array(existing.embedding)
                    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                    
                    if similarity > SIMILARITY_THRESHOLD:
                        logger.info(f"⚠️ Duplicate answer detected (similarity={similarity:.3f}), skipping")
                        return {
                            "status": "skipped", 
                            "reason": "duplicate_answer",
                            "similarity": float(similarity)
                        }
            
            # 5. AnswerBank에 저장
            answer_bank = AnswerBank(
                question_id=question.id,
                answer_text=transcript.text,
                embedding=embedding,
                score=evaluation_score,
                company=question.company,
                industry=question.industry,
                position=question.position,
                evaluator_feedback=None  # 추후 확장 가능
            )
            
            session.add(answer_bank)
            session.commit()
            session.refresh(answer_bank)
            
            logger.info(f"✅ Excellent answer collected (ID={answer_bank.id}, score={evaluation_score}): {transcript.text[:50]}...")
            
            return {
                "status": "success",
                "answer_bank_id": answer_bank.id,
                "score": evaluation_score
            }
            
    except Exception as e:
        logger.error(f"Failed to collect answer: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}


@shared_task(name="tasks.answer_collector.vectorize_existing_questions")
def vectorize_existing_questions(batch_size: int = 100):
    """
    기존 질문들을 배치로 벡터화 (마이그레이션용)
    
    Args:
        batch_size: 한 번에 처리할 질문 개수
    
    Returns:
        dict: 처리 결과
    
    Raises:
        ValueError: 질문이 없거나 벡터화 실패
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    try:
        with Session(engine) as session:
            # embedding이 NULL인 질문들 조회
            from sqlmodel import select
            stmt = select(Question).where(Question.embedding.is_(None)).limit(batch_size)
            questions = session.exec(stmt).all()
            
            if not questions:
                logger.info("No questions to vectorize")
                return {"status": "success", "count": 0}
            
            logger.info(f"Vectorizing {len(questions)} questions...")
            
            # 배치 벡터화
            from vector_utils import get_embedding_generator
            generator = get_embedding_generator()
            
            texts = [q.content for q in questions]
            embeddings = generator.encode_batch(texts)
            
            # DB 업데이트
            for question, embedding in zip(questions, embeddings):
                question.embedding = embedding
                session.add(question)
            
            session.commit()
            
            logger.info(f"✅ Vectorized {len(questions)} questions")
            
            return {
                "status": "success",
                "count": len(questions)
            }
            
    except Exception as e:
        logger.error(f"Vectorization failed: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}
