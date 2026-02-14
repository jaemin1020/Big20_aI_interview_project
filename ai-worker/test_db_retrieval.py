import os
import sys
from sqlmodel import Session, select

# 경로 설정
app_root = "/app"
backend_root = "/backend-core"
if backend_root not in sys.path:
    sys.path.append(backend_root)
if app_root not in sys.path:
    sys.path.append(app_root)

from db import engine
from db_models import Question
from utils.question_retriever import get_question_retriever

def test():
    retriever = get_question_retriever()
    print("Retriever initialized.")
    
    context = "React, Node.js, TypeScript, 백엔드 개발, 성능 최적화"
    print(f"Searching for context: {context}")
    
    questions = retriever.find_relevant_questions(
        text_context=context,
        question_type="직무지식",
        top_k=5
    )
    
    print(f"Found {len(questions)} questions.")
    for i, q in enumerate(questions):
        print(f"{i+1}. {q.content}")

if __name__ == "__main__":
    test()
