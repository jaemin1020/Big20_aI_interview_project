import os
import time
import logging
from sqlmodel import SQLModel, create_engine, Session, text
from sqlalchemy.exc import OperationalError

from models import User, Interview, Transcript, EvaluationReport, Question

# 로깅 설정
logger = logging.getLogger("Database")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# 환경 변수 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# Connection Pool 설정 (프로덕션 성능 최적화)
# - pool_size: 기본적으로 유지할 연결 수
# - max_overflow: pool_size보다 더 많은 연결이 필요할 때 허용할 최대 추가 연결 수
# - pool_recycle: 연결을 재활용할 시간(초) - DB 타임아웃 방지
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 20))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600)) 

engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG_MODE,  # True면 모든 SQL 쿼리가 로그에 남음 (개발용)
    pool_pre_ping=True, # 쿼리 실행 전 연결 상태 확인 (Broken Pipe 방지)
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE
)

def init_db():
    """DB 연결 시도 및 테이블 생성 (Robust Retry Logic)"""
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            logger.info(f"🔄 데이터베이스 연결 시도 중... ({i+1}/{max_retries})")
            
            # 테이블 생성
            SQLModel.metadata.create_all(engine)
            
            # 연결 확인용 간단한 쿼리 실행
            with Session(engine) as session:
                session.exec(text("SELECT 1"))
            
            logger.info("✅ 데이터베이스 테이블 생성 및 연결 성공")
            
            # 초기 데이터 시딩
            seed_initial_data()
            return
        except OperationalError as e:
            if i < max_retries - 1:
                logger.warning(f"⚠️ DB 연결 실패 (아직 준비되지 않음), {retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ DB 연결 실패: {str(e)}")
                raise e

def seed_initial_data():
    """관리자 및 리크루터 초기 계정 생성"""
    from models import User, UserRole
    from utils.auth_utils import get_password_hash
    from sqlmodel import select

    with Session(engine) as session:
        # 1. Admin 계정 생성
        admin_user = session.exec(select(User).where(User.username == "admin")).first()
        if not admin_user:
            logger.info("Creating default Admin account...")
            session.add(User(
                username="admin",
                email="admin@big20.com",
                password_hash=get_password_hash("admin1234"),
                full_name="System Administrator",
                role=UserRole.ADMIN
            ))
        
        # 2. Recruiter 계정 생성
        recruiter_user = session.exec(select(User).where(User.username == "recruiter")).first()
        if not recruiter_user:
            logger.info("Creating default Recruiter account...")
            session.add(User(
                username="recruiter",
                email="recruiter@big20.com",
                password_hash=get_password_hash("recruiter1234"),
                full_name="Lead Recruiter",
                role=UserRole.RECRUITER
            ))
        
        session.commit()
        logger.info("✅ Initial data seeding completed.")

def get_session():
    """FastAPI Dependency Injection용 세션 생성기"""
    with Session(engine) as session:
        yield session