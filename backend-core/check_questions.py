from sqlmodel import Session, select, func
from database import engine
from db_models import Question

with Session(engine) as session:
    count = session.exec(select(func.count(Question.id))).one()
    print(f"Total questions in DB: {count}")
