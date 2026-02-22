from sqlmodel import Session, select, func
from db import engine
from db_models import Question

def check_progress():
    with Session(engine) as session:
        # 전체 질문 수
        total_stmt = select(func.count(Question.id))
        total = session.exec(total_stmt).one()
        
        # 임베딩이 생성된 질문 수
        embedded_stmt = select(func.count(Question.id)).where(Question.embedding != None)
        embedded = session.exec(embedded_stmt).one()
        
        print(f"Total Questions: {total}")
        print(f"Embedded Questions: {embedded}")
        print(f"Progress: {(embedded/total)*100:.2f}%" if total > 0 else "N/A")

if __name__ == "__main__":
    check_progress()
