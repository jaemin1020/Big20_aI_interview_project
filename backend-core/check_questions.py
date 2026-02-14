from sqlmodel import Session, select, func
from database import engine
from db_models import Question

with Session(engine) as session:
    total = session.exec(select(func.count(Question.id))).one()
    embedded = session.exec(select(func.count(Question.id)).where(Question.embedding != None)).one()
    print(f"Total questions in DB: {total}")
    print(f"Embedded questions in DB: {embedded}")
    if total > 0:
        print(f"Progress: {(embedded/total)*100:.2f}%")
