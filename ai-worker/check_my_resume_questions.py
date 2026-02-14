import logging
import os
import sys
import json

# 경로 설정
app_root = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(app_root, "..", "backend-core"))
sys.path.insert(0, backend_root)
sys.path.insert(0, app_root)

from utils.question_retriever import get_question_retriever
from tasks.parse_resume import parse_resume_final
from utils.exaone_llm import get_exaone_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("ResumePersonalizationDemo")

def run_personalization_test(pdf_path: str):
    logger.info(f"--- [1. 이력서 파싱 시작] ---")
    # 도커 내부 경로 후보들
    paths_to_try = [
        f"/app/uploads/{os.path.basename(pdf_path)}",
        f"/backend-core/uploads/{os.path.basename(pdf_path)}",
        f"/app/uploads/test_resume.pdf",  # 리네임된 파일 폴백
        f"/app/{os.path.basename(pdf_path)}"
    ]
    
    docker_pdf_path = None
    for p in paths_to_try:
        if os.path.exists(p):
            docker_pdf_path = p
            break
            
    if not docker_pdf_path:
        logger.error(f"❌ 이력서 파일을 찾을 수 없습니다: {pdf_path}")
        return

    logger.info(f"📂 사용된 이력서 경로: {docker_pdf_path}")
    structured_data = parse_resume_final(docker_pdf_path)
    
    # 이력서의 핵심 내용을 텍스트로 요약 (검색용)
    experience = structured_data.get("experience", [])
    projects = structured_data.get("projects", [])
    skills = structured_data.get("skills", [])
    self_intro = structured_data.get("self_intro", [])
    candidate_name = structured_data.get('header', {}).get('name') or "김린"
    
    print("\n" + "-"*30)
    print(f"📄 파싱된 이력서 정보 ({candidate_name} 지원자)")
    print(f"이름: {candidate_name}")
    print(f"기술: {', '.join(skills) if skills else '추출된 기술 없음'}")
    print(f"프로젝트 수: {len(projects)}")
    print(f"자소서 문항 수: {len(self_intro)}")
    print("-"*30)
    
    # 검색 문맥 구성 (더 풍부하게)
    summary_for_search = ""
    if skills:
        summary_for_search += f"기술 스택 및 역량: {', '.join(skills)}\n"
    
    if projects:
        for p in projects[:2]:
            summary_for_search += f"프로젝트: {p.get('title')} - {p.get('description')}\n"
            
    if self_intro:
        # 첫 번째 자소서 문항 답변 요약
        first_intro = self_intro[0].get("answer", "")[:200]
        summary_for_search += f"자기소개 핵심: {first_intro}\n"

    logger.info(f"--- [2. 질문 은행에서 유사 질문 추출] ---")
    retriever = get_question_retriever()
    # 이력서 맥락과 가장 유사한 질문 Top 5 추출
    base_questions = retriever.find_relevant_questions(
        text_context=summary_for_search,
        question_type="직무지식",
        top_k=5
    )
    
    print("\n" + "="*60)
    print(f"🔍 [김린 지원자] AI 질문 은행(6만 개) 기반 상위 질문 5개")
    print("="*60)
    for idx, q in enumerate(base_questions):
        # 실제 환경에서는 q.distance 등으로 관련도 체크 가능
        print(f"{idx+1}. [{q.category}] {q.content}")
    print("-" * 60)

    logger.info(f"--- [3. LLM을 통한 초개인화 질문 생성] ---")
    llm = get_exaone_llm()
    prompt = PromptTemplate.from_template("""[|system|]
너는 대한민국 최고의 기술 면접관이다. DB에서 추출된 '기본 질문'과 지원자의 '이력서 내용'을 결합하여, 
오직 이 지원자만을 위한 날카로운 '초개인화 질문'을 1개 생성하라.

[김린 지원자 정보]
{resume_info}

[DB 추출 기본 질문 후보]
{base_question}

[지침]
1. 이력서에 언급된 구체적인 프로젝트나 기술 스택을 반드시 언급하며 질문을 시작할 것.
2. DB 질문의 핵심 개념을 지원자의 경험과 연결하여 질문할 것.
3. 150자 이내, 두 문장으로 간결하게 작성할 것.
[|endofturn|]
[|user|]
김린 지원자 맞춤형 면접 질문을 생성해줘.
[|endofturn|]
[|assistant|]
""")
    
    chain = prompt | llm | StrOutputParser()
    
    # 상위 5개 질문 중 가장 관련성 높은 첫 번째 질문을 기반으로 개인화 시도
    if base_questions:
        target_q = base_questions[0]
        personalized_q = chain.invoke({
            "resume_info": summary_for_search,
            "base_question": target_q.content
        })
        
        print("\n" + "✨" * 30)
        print("🚀 [최종 탄생한 초개인화 질문]")
        print(f"기반이 된 DB 질문: {target_q.content}")
        print(f"👉 김린님 전용 질문: {personalized_q}")
        print("✨" * 30 + "\n")

if __name__ == "__main__":
    pdf_file = "김린_신입_이력서.pdf"
    run_personalization_test(pdf_file)
