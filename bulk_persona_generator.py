import os
import sys
import json
import random
import logging
from datetime import datetime
import numpy as np

# ==========================================================
# [Windows GPU FIX] CUDA DLL 경로 문제 해결을 위한 로직
# ==========================================================
if os.name == 'nt':
    possible_paths = []
    cuda_path = os.environ.get('CUDA_PATH')
    if cuda_path:
        possible_paths.append(os.path.join(cuda_path, 'bin'))
    
    base_cuda = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if os.path.exists(base_cuda):
        try:
            versions = os.listdir(base_cuda)
            for v in versions:
                if v.startswith('v'):
                    possible_paths.append(os.path.join(base_cuda, v, 'bin'))
        except:
            pass

    for path in possible_paths:
        if os.path.exists(path):
            try:
                os.add_dll_directory(path)
            except:
                pass
# ==========================================================

# 환경 변수 설정
os.environ["USE_GPU"] = "true"
os.environ["N_GPU_LAYERS"] = "35"

import time

# 프로젝트 루트 경로 추가
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(root_dir)
# 하이픈이 포함된 폴더를 직접 path에 추가하여 내부 모듈을 바로 임포트 가능하게 함
sys.path.append(os.path.join(root_dir, "ai-worker"))
sys.path.append(os.path.join(root_dir, "backend-core"))

# [중요] Docker 밖(로컬 CMD)에서 실행할 때를 위한 DB 경로 설정
# db:5432는 도커 전용이므로, 로컬 접속용 포트인 15432와 localhost로 변경
if not os.environ.get("DATABASE_URL") or "db:5432" in os.environ.get("DATABASE_URL", ""):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"
    # redis_url 등 다른 환경변수도 로컬 버전이 필요하다면 여기서 설정 가능

# 모듈 임포트 (순서 주의: path 설정 후 임포트)
from utils.exaone_llm import get_exaone_llm
from utils.vector_utils import get_embedding_generator
from utils.question_retriever import get_question_retriever
from tasks.chunking import chunk_resume
from db import engine, save_generated_question
from db_models import User, Resume, Interview, InterviewStatus, Question, QuestionCategory
from sqlmodel import Session, select
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

# 시나리오 임포트
import config.interview_scenario as std_scenario
import config.interview_scenario_transition as trans_scenario

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bulk_gen_final.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 프롬프트 템플릿 (지원자 전공 정보 추가)
PROMPT_TEMPLATE = """
당신은 대한민국 최고의 전문 면접관입니다. 
가상 지원자 {name}님의 {position} 직무 면접을 진행하고 있습니다.

[지원자 이력서 요약]
- 이름: {name}
- 전공: {major}
- 현재 지원 부서: {position}
- 핵심 프로젝트: {project_title}
- 관련 컨텍스트: {context}

[현재 면접 단계]
단계명: {stage_name}
평가 가이드: {guide}

[참고 질문 세트]
{db_questions}

[임무]
1. 위 컨텍스트(특히 전공과 지원직무의 연관성)와 가이드를 바탕으로, 지원자의 경험을 깊이 있게 검증할 수 있는 면접 질문을 1개만 생성하세요.
2. 만약 전공({major})과 지원직무({position})가 상이하다면, 왜 전공을 살리지 않고 이 길을 택했는지, 혹은 전공 지식이 이 직무에 어떻게 기여할 수 있는지에 대한 문맥을 질문에 자연스럽게 녹여내세요.
3. AI가 생성한 느낌이 들지 않도록 자연스럽고 정중한 말투를 사용하세요.
4. 질문의 서두에 반드시 상황에 맞는 공감이나 리액션(예: "아, 그러시군요", "흥미진진한 프로젝트네요")을 포함하세요.
5. 질문만 출력하세요. 불필요한 서술은 제외하세요.
"""

def get_exaone_llm_ollama():
    try:
        return OllamaLLM(model="exaone3.5:latest", temperature=0.7)
    except Exception:
        return get_exaone_llm()

# 중복 방지를 위한 글로벌 레지스트리
used_names = set()
used_projects = set()
used_companies = set()
used_majors = set()

def load_existing_data():
    """DB에서 기존 데이터를 로드하여 중복 방지 세트 초기화"""
    try:
        with Session(engine) as session:
            # 기존 유저 이름 및 전공 로드
            users = session.exec(select(User.full_name)).all()
            for name in users:
                if name: used_names.add(name)
            
            # Resume에서 전공 정보 수집
            resumes = session.exec(select(Resume.structured_data)).all()
            for data in resumes:
                if data and 'header' in data:
                    major = data['header'].get('major')
                    if major: used_majors.add(major)
            
            logger.info(f"✅ 기존 데이터 로드 완료: 이름 {len(used_names)}개, 전공 {len(used_majors)}개")
    except Exception as e:
        logger.warning(f"⚠️ 기존 데이터 로드 중 오류 (무시하고 진행): {e}")

def generate_persona(llm, position):
    """절대 중복되지 않는 페르소나 생성 (전공 다양성 강화)"""
    global used_names, used_projects, used_companies, used_majors
    
    avoid_names = list(used_names)[-20:]
    avoid_projects = list(used_projects)[-20:]
    avoid_majors = list(used_majors)[-10:]

    # AI에게 던져줄 다양한 비전공 리스트 (예시)
    major_samples = ["국어국문학", "철학", "심리학", "사회학", "경제학", "경영학", "신문방송학", "정치외교학", "법학", "행정학", 
                     "영어영문학", "중어중문학", "일어일문학", "사학", "지리학", "의상디자인", "조리외식경영", "식품영양학", 
                     "간호학", "물리치료학", "체육학", "사회복지학", "문헌정보학", "유아교육학", "실용음악", "회화", "조소"]
    
    prompt = f"""
    대한민국 IT 기업에 지원하는 {position} 신입/경험자 1명의 상세 가상 페르소나를 JSON 형식으로 생성하세요.
    [필수 서사] 반드시 해당 직무와 관련 없는 비전공자나 직무 전환자 서사를 부여하세요.
    
    [전공 다양성 가이드] 
    - 아래 예시 리스트 중 하나를 참고하거나, 이와 비슷한 비IT 계열 전공을 자유롭게 선택하세요.
    - 예시: {major_samples}
    - 절대 피해야 할 최근 전공: {avoid_majors} (특히 '미술사'가 너무 많으니 절대 피할 것)

    [중요: 절대 중복 금지 규칙]
    1. 이름: 아래 리스트에 없는 아주 희귀하거나 새로운 이름을 사용하세요.
       (피해야 할 이름: {avoid_names})
    2. 프로젝트: 아래와 겹치지 않는 매우 구체적이고 독특한 시나리오를 만드세요.
       (피해야 할 프로젝트 키워드: {avoid_projects})
    3. 회사: 대기업 외에 유망한 스타트업이나 가상의 기업 이름을 창조해도 좋습니다.
    
    [응답 형식]
    {{
        "header": {{
            "name": "이름",
            "target_role": "{position}",
            "target_company": "지원이유가 명확한 회사명",
            "major": "실제 전공",
            "is_career_changer": true/false (불리언값)
        }},
        "education": [{{ "school_name": "대학교명", "major": "전공명", "status": "졸업" }}],
        "projects": [
            {{
                "title": "중복되지 않는 고유한 프로젝트명",
                "description": "상세한 기술적 설명"
            }}
        ],
        "self_intro": [
            {{ "question": "지원동기", "answer": "상세한 답변 내용..." }}
        ]
    }}
    """
    
    for attempt in range(3):
        try:
            response = llm.invoke(prompt)
            
            # JSON 추출 로직 강화 (raw_decode 사용)
            content = response.strip()
            start_idx = content.find('{')
            if start_idx == -1:
                logger.error("❌ 응답에서 '{'를 찾을 수 없습니다.")
                continue
            
            try:
                decoder = json.JSONDecoder()
                persona, end_idx = decoder.raw_decode(content[start_idx:])
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 디코딩 실패 (시도 {attempt+1}): {e}")
                continue
            
            name = persona['header']['name']
            proj = persona['projects'][0]['title']
            comp = persona['header']['target_company']
            
            if name in used_names or proj in used_projects:
                logger.warning(f"🔄 중복 발견 ({name} 또는 {proj}), 재생성 시도중... ({attempt+1}/3)")
                continue
                
            used_names.add(name)
            used_projects.add(proj)
            used_companies.add(comp)
            return persona
            
        except Exception as e:
            logger.error(f"❌ 페르소나 파싱 에러: {e}")
            continue
    return None

def main():
    logger.info("🚀 벌크 생성기 시작 (Ollama + 백업 + 중복방지 모드)...")
    
    load_existing_data()
    
    try:
        llm = get_exaone_llm_ollama()
        retriever = get_question_retriever()
        embedder = get_embedding_generator()
        logger.info("✅ 엔진 로드 완료")
    except Exception as e:
        logger.error(f"❌ 엔진 로드 실패: {e}")
        return

    target_positions = ["백엔드개발자", "프론트엔드개발자", "데이터분석가", "AI개발자", "PL·PM·PO"]
    
    target_count = 50
    if len(sys.argv) > 1:
        try: target_count = int(sys.argv[1])
        except: pass
            
    BATCH_SIZE = 50
    total_generated = 0
    all_results = []
    
    backup_dir = os.path.join(root_dir, "generated_data")
    os.makedirs(backup_dir, exist_ok=True)

    while total_generated < target_count:
        current_batch = min(BATCH_SIZE, target_count - total_generated)
        logger.info(f"\n📢 [BATCH START] 목표: {current_batch}명 (누적: {total_generated}/{target_count})")
        
        for i in range(current_batch):
            pos = random.choice(target_positions)
            logger.info(f"\n{'#'*60}")
            logger.info(f"[{total_generated + i + 1}/{target_count}] 👷 {pos} 생성 중...")
            
            persona = generate_persona(llm, pos)
            if not persona: continue
            
            name = persona['header']['name']
            role = persona['header']['target_role']
            is_transition = persona['header'].get('is_career_changer', False)
            
            # 1. DB 저장 (유저, 이력서, 인터뷰)
            interview_id = None
            try:
                with Session(engine) as session:
                    user = User(
                        username=f"fake_{name}_{random.randint(1000,9999)}", 
                        email=f"{name}{random.randint(1000,9999)}@test.com", 
                        full_name=name, 
                        password_hash="dummy"
                    )
                    session.add(user); session.commit(); session.refresh(user)
                    
                    resume = Resume(
                        candidate_id=user.id, file_name=f"virtual_{name}.pdf", 
                        file_path="VIRTUAL", file_size=0, 
                        target_position=role, structured_data=persona, processing_status="completed"
                    )
                    session.add(resume); session.commit(); session.refresh(resume)
                    
                    interview = Interview(
                        candidate_id=user.id, resume_id=resume.id, 
                        position=role, status=InterviewStatus.COMPLETED
                    )
                    session.add(interview); session.commit(); session.refresh(interview)
                    interview_id = interview.id
                logger.info(f"✅ 가상 지원자 [{name}] DB 등록 완료 (직무전환: {is_transition})")
            except Exception as e:
                logger.error(f"❌ DB 등록 실패: {e}")
                continue

            # 2. 질문 생성 파이프라인
            backup_candidate = { "persona": persona, "generated_questions": [] }
            try:
                # 시나리오 선택
                stages = trans_scenario.INTERVIEW_STAGES if is_transition else std_scenario.INTERVIEW_STAGES
                
                chunks = chunk_resume(persona)
                chunk_texts = [c['text'] for c in chunks]
                chunk_embeddings = embedder.encode_batch(chunk_texts, is_query=False)
                
                last_primary_question = ""
                prompt_tpl = PromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt_tpl | llm | StrOutputParser()
    
                for stage in stages:
                    stage_name = stage['stage']
                    
                    # 자기소개, 지원동기, 최종발언 단계는 제외 (사용자 요청)
                    if stage_name in ['intro', 'motivation', 'final_statement']:
                        continue
                        
                    order = stage['order']
                    persona_major = persona['header'].get('major', '이전 전공')
                    
                    if stage['type'] == 'template':
                        # 템플릿 질문은 즉시 저장
                        content = stage['template'].format(
                            candidate_name=name, 
                            target_role=role, 
                            major=persona_major
                        )
                        save_generated_question(interview_id, content, "behavioral", stage['stage'], "", position=role)
                        backup_candidate["generated_questions"].append({"order": order, "stage": stage['stage'], "content": content})
                        continue
                    
                    stage_name = stage['stage']
                    stage_type = stage['type']
                    # 가이드에 {major}가 포함되어 있을 경우 실제 전공으로 치환
                    guide = stage.get('guide', '').format(major=persona_major, target_role=role)
                    
                    final_content = ""
                    try:
                        if stage_type == "ai":
                            query_vec = embedder.encode_query(f"{stage_name} {guide}")
                            scores = [np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb)) for emb in chunk_embeddings]
                            top_idx = np.argsort(scores)[::-1][:3]
                            ctx = "\n".join([chunk_texts[idx] for idx in top_idx])
                            
                            db_qs = retriever.find_relevant_questions(text_context=ctx, question_type=stage_name, top_k=5)
                            db_qs_str = "\n".join([f"{idx+1}. {q.content}" for idx, q in enumerate(db_qs)])
                            
                            final_content = chain.invoke({
                                "stage_name": stage_name, "guide": guide, "name": name, 
                                "major": persona_major,
                                "context": ctx, "db_questions": db_qs_str,
                                "position": pos, "project_title": persona['projects'][0]['title']
                            })
                            last_primary_question = final_content
                            
                        elif stage_type == "followup":
                            final_content = chain.invoke({
                                "stage_name": stage_name, "guide": guide, "name": name,
                                "major": persona_major,
                                "context": f"이전 질문: {last_primary_question}\n(면접관으로서 꼬리질문을 던지는 상황)", 
                                "db_questions": f"{persona_major} 전공자가 기술적 깊이를 증명해야 하는 꼬리질문 생성",
                                "position": pos, "project_title": persona['projects'][0]['title']
                            })
    
                        if final_content:
                            save_generated_question(interview_id, final_content, "technical", stage_name, guide, position=role, company=persona['header'].get('target_company'))
                            backup_candidate["generated_questions"].append({"order": order, "stage": stage_name, "content": final_content, "guide": guide})
                            logger.info(f"  [{order:02d}] {stage_name} 생성 완료")
                    except Exception as e:
                        logger.error(f"❌ 질문 생성 에러 (Stage: {stage_name}): {e}")
                
                # 결과 수집 (메모리에 저장 후 마지막에 한꺼번에 엑스포트)
                all_results.append(backup_candidate)
            except Exception as e:
                logger.error(f"❌ 전체 파이프라인 에러: {e}")
                
        total_generated += current_batch
        if total_generated < target_count:
            logger.info("💤 배치 완료. 10초 대기 후 재개...")
            time.sleep(10)

    # 최종 엑스포트
    if all_results:
        final_file = f"bulk_final_{int(time.time())}.json"
        with open(os.path.join(backup_dir, final_file), 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        logger.info(f"✨ [CSV/JSON Export] {len(all_results)}명의 데이터 최종 백업 완료: {final_file}")

if __name__ == "__main__":
    main()
