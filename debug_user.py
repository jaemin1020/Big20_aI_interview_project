from sqlmodel import Session, create_engine, select
from db_models import User
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lsj:lsj1234@localhost:5432/interview_db")
engine = create_engine(DATABASE_URL)

def check_user(username):
    with Session(engine) as session:
        statement = select(User).where(User.username == username)
        results = session.exec(statement).all()
        print(f"--- Records for username: {username} ---")
        for user in results:
            print(f"ID: {user.id}, Username: {user.username}, Is Withdrawn: {user.is_withdrawn}, Withdrawn At: {user.withdrawn_at}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        check_user(sys.argv[1])
    else:
        print("Please provide a username.")
