import logging
import os
import sys

# 경로 설정
app_root = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(app_root, "..", "backend-core"))
sys.path.insert(0, backend_root)
sys.path.insert(0, app_root)

from utils.question_retriever import get_question_retriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("RetrievalDemo")

def run_demo():
    retriever = get_question_retriever()
    
    # 테스트 케이스 1: React 개발자 이력서 문구
    test_context = "React와 Redux를 사용해서 프론트엔드 성능을 최적화하고 복잡한 상태 관리를 해결했습니다."
    print(f"\n[입력 문맥]: {test_context}")
    
    questions = retriever.find_relevant_questions(
        text_context=test_context,
        question_type="직무지식",
        top_k=3
    )
    
    print("\n[추출된 맞춤형 질문 (Top 3)]")
    for idx, q in enumerate(questions):
        print(f"{idx+1}. [{q.category}] {q.content} (직무: {q.position})")

    # 테스트 케이스 2: Java 백엔드 개발자
    test_context2 = "Java Spring Boot와 JPA를 사용하여 RESTful API를 설계하고 데이터베이스 병목 지점을 해결했습니다."
    print(f"\n[입력 문맥]: {test_context2}")
    
    questions2 = retriever.find_relevant_questions(
        text_context=test_context2,
        question_type="직무지식",
        top_k=3
    )
    
    print("\n[추출된 맞춤형 질문 (Top 3)]")
    for idx, q in enumerate(questions2):
        print(f"{idx+1}. [{q.category}] {q.content} (직무: {q.position})")

if __name__ == "__main__":
    run_demo()
