import sys, os
from sqlmodel import Session, select, text
from sentence_transformers import SentenceTransformer
sys.path.append('/app')
from database import engine
from models import Question, AnswerBank, Resume

def migrate():
    print('Starting Migration...')
    sqls = [
        'UPDATE questions SET embedding = NULL',
        'UPDATE answer_bank SET embedding = NULL',
        'ALTER TABLE questions ALTER COLUMN embedding TYPE vector(1024)',
        'ALTER TABLE answer_bank ALTER COLUMN embedding TYPE vector(1024)'
    ]
    with Session(engine) as session:
        for sql in sqls:
            try:
                session.exec(text(sql))
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)
    
    print('Re-embedding...')
    model = SentenceTransformer('BAAI/bge-m3')
    with Session(engine) as session:
        qs = session.exec(select(Question)).all()
        for q in qs:
            if q.content: q.embedding = model.encode(q.content, normalize_embeddings=True).tolist()
        ans = session.exec(select(AnswerBank)).all()
        for a in ans:
            if a.answer_text: a.embedding = model.encode(a.answer_text, normalize_embeddings=True).tolist()
        session.commit()
    print('Done!')

if __name__ == '__main__':
    migrate()
