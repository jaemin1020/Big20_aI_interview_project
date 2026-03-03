import logging
import os
import json
from celery import shared_task, current_app
from sqlmodel import Session

# [문법] __name__: 현재 모듈의 이름을 자동으로 가져옵니다. 
# 로그에 어느 파일에서 발생한 일인지 찍어주는 이정표가 됩니다.
logger = logging.getLogger(__name__)

# [문법] try-except: 임포트 에러가 나더라도 전체 서버가 죽지 않게 보호합니다.
# 특히 DB 모델은 다른 파일에서 가져오기 때문에 경로 문제가 생길 수 있어 안전장치를 둔 것입니다.
try:
    from db_models import Resume
    from db import engine
except ImportError as e:
    logger.error(f"❌ Critical Import Error in resume_parser: {e}")
    
# 앞서 우리가 분석했던 파싱 함수를 가져옵니다.
from .parse_resume import parse_resume_final

logger.info("✅ Task Module 'tasks.resume_pipeline' is being loaded.")

# ==========================================
# 메인 작업: 이력서 파이프라인 (parse_resume_pdf)
# ==========================================

# [문법] bind=True: 이 함수가 Celery 작업 자체의 속성(예: 재시도 횟수 등)에 접근할 수 있게 'self'를 첫 번째 인자로 받습니다.
# [문법] queue='cpu_queue': 이 작업은 연산량이 많으므로 'CPU 전용 일꾼'에게만 시키겠다는 명시적인 지정입니다.
@shared_task(bind=True, name="tasks.resume_pipeline.parse_pdf", queue='cpu_queue')
def parse_resume_pdf(self, resume_id: int, file_path: str):
    """
    이력서 PDF를 읽어 DB에 저장하고, 다음 AI 단계로 넘기는 '공장장' 함수
    """
    
    # -------------------------------------------------------
    # 1. 파일 경로 정규화 (Docker/컨테이너 환경 대응)
    # -------------------------------------------------------
    # [해석] 서버(Backend)와 일꾼(Worker)은 서로 다른 컨테이너일 수 있습니다.
    # 서버가 알려준 경로가 일꾼 입장에서는 다를 수 있기 때문에, 컨테이너 내 공통 경로(/app/uploads/resumes)로 강제 조정합니다.
    filename = os.path.basename(file_path) # 파일명만 쏙 뽑기 (예: "my_resume.pdf")
    normalized_path = os.path.join("/app/uploads/resumes", filename)
    
    logger.info(f"🚀 [START] Resume parsing ID: {resume_id}")
    
    try:
        # 파일이 실제로 있는지 확인 (없으면 파싱을 못 하니까요!)
        if not os.path.exists(normalized_path):
            logger.error(f"❌ File not found: {normalized_path}")
            # 폴백: 정규화된 경로에 없으면 원래 경로로라도 한 번 더 시도해봅니다.
            if os.path.exists(file_path):
                normalized_path = file_path
            else:
                # 둘 다 없으면 실패 처리하고 종료
                _update_status(resume_id, "failed")
                return
            
        # -------------------------------------------------------
        # 2. 파싱 실행 (우리가 만든 엔진 가동)
        # -------------------------------------------------------
        logger.info(f"🔍 Parsing PDF...")
        parsed_data = parse_resume_final(normalized_path)
        logger.info(f"✅ Parsing Success: {parsed_data.get('header', {}).get('name')} detected")
        
        # -------------------------------------------------------
        # 3. DB 업데이트 (SQLModel 사용)
        # -------------------------------------------------------
        # [문법] with Session(engine) as session: DB 연결을 열고, 작업이 끝나면 자동으로 닫아주는 문법입니다.
        with Session(engine) as session:
            # DB에서 해당 ID의 이력서 정보를 가져옵니다.
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"❌ Resume {resume_id} not found in DB")
                return

            # 파싱된 결과(JSON 형태)를 DB 컬럼에 저장합니다.
            resume.structured_data = parsed_data
            
            # 파서가 찾아낸 '지원 직무'가 있다면 DB에 따로 기록해줍니다.
            target_pos = parsed_data.get("header", {}).get("target_role")
            if target_pos:
                resume.target_position = target_pos
                
            # [문법] json.dumps: 파이썬 딕셔너리를 텍스트 형태의 JSON으로 변환하여 DB에 넣기 좋게 만듭니다.
            resume.extracted_text = json.dumps(parsed_data, ensure_ascii=False)
            
            # 현재 상태를 '처리 중(processing)'으로 바꿉니다. (다음 단계인 임베딩이 남았으므로)
            resume.processing_status = "processing" 
            
            session.add(resume) # 변경사항 등록
            session.commit()    # DB에 최종 저장!
            logger.info(f"💾 DB Updated for Resume {resume_id}")
            
        # -------------------------------------------------------
        # 4. 다음 단계(임베딩) 호출 - 릴레이 경주!
        # -------------------------------------------------------
        # [해석] 파싱이 끝났으니, 이제 이걸 벡터 데이터로 바꿀 'GPU 전용 일꾼'에게 일을 넘깁니다.
        # [문법] send_task: 다른 파일에 정의된 Celery 작업을 이름만으로 호출할 수 있습니다.
        current_app.send_task(
            "tasks.resume_pipeline.generate_embeddings",
            args=[resume_id],
            queue='gpu_queue' # 임베딩은 GPU 서버가 처리
        )
        logger.info(f"➡️ [NEXT] Sent embedding task for Resume {resume_id}")

    except Exception as e:
        # 에러 발생 시 로그를 남기고 DB 상태를 'failed'로 변경합니다.
        logger.error(f"Error parsing resume {resume_id}: {e}", exc_info=True)
        _update_status(resume_id, "failed")

# ==========================================
# 보조 함수: 상태 업데이트 (DRY 원칙)
# ==========================================

def _update_status(resume_id: int, status: str):
    """
    이 함수는 코드 중복을 피하기 위해 만든 '상태 업데이트 전용' 함수입니다.
    함수 이름 앞에 언더바(_)를 붙여서 '이 파일 안에서만 주로 쓰겠다'는 신호를 줍니다.
    """
    with Session(engine) as session:
        resume = session.get(Resume, resume_id)
        if resume:
            resume.processing_status = status
            session.add(resume)
            session.commit()