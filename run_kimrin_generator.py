import os
import sys
import logging
print("DEBUG: Core modules imported", flush=True)

# [1. 경로 설정] 현재 실행 위치(루트)를 기준으로 경로 추가
root_dir = os.path.dirname(os.path.abspath(__file__))
# 루트 폴더를 path에 추가하여 패키지명(ai_worker, backend_core)으로 접근 가능하게 함
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 환경 변수에 따라 DB 연결 설정 (로컬 실행용)
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"

print(f"DEBUG: sys.path updated with {root_dir}", flush=True)

try:
    print("DEBUG: Importing modules...", flush=True)
    # ai-worker.utils 와 backend-core.utils 명칭 충돌을 피하기 위해 
    # 서브디렉토리를 직접 추가하여 모듈을 임포트합니다.
    ai_worker_path = os.path.join(root_dir, "ai-worker")
    ai_worker_utils_path = os.path.join(ai_worker_path, "utils")
    backend_core_path = os.path.join(root_dir, "backend-core")
    
    # 순서: ai-worker/utils를 최상단에 추가
    sys.path.insert(0, backend_core_path)
    sys.path.insert(0, ai_worker_path)
    sys.path.insert(0, ai_worker_utils_path) 
    
    from db import engine, save_generated_question
    from db_models import Question, User, Resume, Interview, InterviewStatus
    from config.interview_scenario import INTERVIEW_STAGES
    from tasks.parse_resume import parse_resume_final
    from tasks.chunking import chunk_resume
    
    # utils.xxx 대신 xxx 로 직접 임포트 (ai-worker/utils가 path에 먼저 있으므로)
    import question_retriever
    import exaone_llm
    import vector_utils
    get_question_retriever = question_retriever.get_question_retriever
    get_exaone_llm = exaone_llm.get_exaone_llm
    get_embedding_generator = vector_utils.get_embedding_generator
except ImportError as e:
    print(f"❌ 임포트 실패: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ 기타 오류: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

from sqlmodel import Session, select
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("InterviewPipeline")

# [2. 프롬프트 템플릿]
PROMPT_TEMPLATE = """[|system|]
너는 전문 면접관이다. 지원자의 [이력서 맥락]과 DB에서 검색된 [참조 질문 5개]를 바탕으로, 
해당 지원자에게만 던질 수 있는 구체적인 질문 1개를 생성하라.

[규칙]
1. 답변은 반드시 한국어로, 두 문장 이내(150자)로 작성하라.
2. DB 참조 질문의 핵심 의도를 유지하되, 지원자의 구체적인 프로젝트나 기술 스택 내용을 문장에 녹여라.
3. 현재 면접 단계의 [평가 가이드]를 엄격히 준수하라.
[|endofturn|]
[|user|]
# 면접 단계: {stage_name}
# 평가 가이드: {guide}
# 지원자 성함: {name}
# 이력서 맥락: {context}

# DB 검색된 참조 질문 (이 중 가장 적절한 의도를 선택해서 변형):
{db_questions}

# 요청: 위 정보를 종합하여 {name} 지원자만을 위한 날카로운 질문 1개를 생성해줘.
[|endofturn|]
[|assistant|]
"""

import numpy as np

def main():
    target_pdf = "김린_신입_삼성-ai개발자이력서.pdf"
    if not os.path.exists(target_pdf):
        print(f"❌ 파일을 찾을 수 없습니다: {target_pdf}")
        return

    # 1. 이력서 분석 (Tasks 활용)
    print("📄 1단계: 이력서 파싱 및 청킹 중...")
    parsed_data = parse_resume_final(target_pdf)
    if not parsed_data:
        print("❌ 이력서 파싱 실패")
        return

    # 이력서 내 헤더 정보에서 이름과 직무 자동 추출
    header = parsed_data.get("header", {})
    name = header.get("name") or "김린"
    target_role = header.get("target_role") or "소프트웨어 개발자"

    print(f"🚀 [{name}] 지원자 ({target_role}) 맞춤형 15개 질문 생성 및 DB 저장 시작\n")
    
    # [DB 준비] 사용자, 이력서, 면접 세션 생성
    with Session(engine) as session:
        # 1. 사용자 조회 또는 생성
        user = session.exec(select(User).where(User.full_name == name)).first()
        if not user:
            user = User(
                username=f"user_{name}", 
                email=f"{name}@example.com", 
                full_name=name,
                password_hash="dummy" # 실제 로그인 용이 아님
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"👤 새 사용자 생성 완료: {name}")

        # 2. 이력서 레코드 생성 (파일은 이미 존재함)
        resume = Resume(
            candidate_id=user.id,
            file_name=os.path.basename(target_pdf),
            file_path=os.path.abspath(target_pdf),
            file_size=os.path.getsize(target_pdf),
            target_position=target_role,
            structured_data=parsed_data,
            processing_status="completed"
        )
        session.add(resume)
        session.commit()
        session.refresh(resume)
        print(f"📄 이력서 DB 등록 완료 (ID: {resume.id})")

        # 3. 면접 세션 생성
        interview = Interview(
            candidate_id=user.id,
            resume_id=resume.id,
            position=target_role,
            status=InterviewStatus.LIVE
        )
        session.add(interview)
        session.commit()
        session.refresh(interview)
        interview_id = interview.id
        print(f"🎤 면접 세션 생성 완료 (ID: {interview_id})")

    chunks = chunk_resume(parsed_data)
    # 2. 유틸리티 준비
    retriever = get_question_retriever()
    llm = get_exaone_llm()
    embedder = get_embedding_generator()
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    print("🔍 이력서 청크 임베딩 생성 중 (검색 최적화)...", flush=True)
    chunk_texts = [c['text'] for c in chunks]
    chunk_embeddings = embedder.encode_batch(chunk_texts, is_query=False)

    generated_questions = []
    last_primary_question = "" 

    # 3. 15개 단계 순회
    for stage in INTERVIEW_STAGES:
        order = stage['order']
        stage_name = stage['stage']
        stage_type = stage['type']
        guide = stage.get('guide', '')

        print(f"\n{'='*60}")
        print(f"📌 [질문 {order:02d}] 단계: {stage_name} ({stage_type})")
        
        final_content = ""
        category = "technical" # 기본 값

        if stage_type == "template":
            tmpl = stage['template']
            final_content = tmpl.format(candidate_name=name, target_role=target_role)
            print(f"💬 [Template] {final_content}")

        # 3번부터 AI 생성 (RAG 적용)
        elif stage_type == "ai":
            # [Step 1: 현재 단계에 적합한 이력서 맥락 찾기]
            print(f"📋 '{stage_name}' 관련 이력서 내용 매칭 중...", flush=True)
            stage_vec = embedder.encode_query(f"{stage_name} {guide}")
            
            scores = []
            for emb in chunk_embeddings:
                sim = np.dot(stage_vec, emb) / (np.linalg.norm(stage_vec) * np.linalg.norm(emb))
                scores.append(sim)
            
            top_indices = np.argsort(scores)[::-1][:3]
            stage_resume_context = "\n".join([chunk_texts[i] for i in top_indices])
            
            print(f"--- [Applied Resume Context] ---", flush=True)
            for i in top_indices:
                print(f"   - {chunk_texts[i]} (Score: {scores[i]:.4f})", flush=True)
            print(f"--------------------------------", flush=True)

            # [Step 2: 검색된 이력서 맥락 기반 DB 검색]
            print(f"🔍 DB에서 '{stage_name}' 관련 유사 질문 5개 검색 중...", flush=True)
            db_results = retriever.find_relevant_questions(
                text_context=stage_resume_context,
                question_type=stage_name, 
                top_k=5
            )
            
            if len(db_results) < 5:
                 db_results = retriever.find_relevant_questions(
                    text_context=stage_resume_context,
                    top_k=10
                )[:5]

            db_questions_str = ""
            print(f"--- [DB Search Logs: Reference Questions (Cosine Similarity)] ---", flush=True)
            if not db_results:
                print("   (유사 질문 없음 - 일반 지식 기반 생성)", flush=True)
                db_questions_str = "참조할 DB 질문 없음."
            else:
                for i, q in enumerate(db_results):
                    print(f"   [{i+1}] {q.content} (ID: {q.id})", flush=True)
                    db_questions_str += f"{i+1}. {q.content}\n"
            print(f"-------------------------------------------------------------", flush=True)

            # LLM 호출
            final_content = chain.invoke({
                "stage_name": stage_name,
                "guide": guide,
                "name": name,
                "context": stage_resume_context,
                "db_questions": db_questions_str
            })
            
            print(f"🤖 [Personalized] {final_content}")
            last_primary_question = final_content

        # 꼬리질문 (Followup)
        elif stage_type == "followup":
            followup_prompt = f"방금 {name}님에게 '{last_primary_question}'라고 질문했습니다. 이 질문의 답변에서 나올 수 있는 예상 꼬리질문을 '{guide}' 의도에 맞게 생성하세요."
            
            final_content = chain.invoke({
                "stage_name": stage_name,
                "guide": guide,
                "name": name,
                "context": followup_prompt,
                "db_questions": "이전 질문 기반 꼬리질문생성이므로 DB 검색 생략"
            })
            print(f"↪️ [Follow-up] {final_content}")

        # [DB 저장] 생성된 질문 저장 (1, 2, 15번 제외)
        if final_content:
            if order not in [1, 2, 15]:
                save_generated_question(
                    interview_id=interview_id,
                    content=final_content,
                    category=category,
                    stage=stage_name,
                    guide=guide
                )
            generated_questions.append(final_content)

    # 4. 최종 결과 요약
    print(f"\n\n{'*'*20} 생성 완료 {'*'*20}")
    print(f"총 {len(generated_questions)}개의 질문이 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    main()
