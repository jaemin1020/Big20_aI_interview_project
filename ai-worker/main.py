import logging
from celery import Celery
import multiprocessing

# CUDA 호환성을 위해 spawn 방식 사용
multiprocessing.set_start_method('spawn', force=True)

# 1. 로깅 설정 (JSON/로그 원칙)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("AI-Worker-Core")

# 2. Celery 앱 설정
import os

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
app = Celery(
    "ai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    broker_connection_retry_on_startup=True,  # Celery 6.0 호환성
    include=['tasks.evaluator', 'tasks.vision', 'tasks.question_generator', 'tasks.resume_parser', 'tasks.answer_collector', 'tasks.search_helper', 'tasks.resume_embedding', 'tasks.stt']
)

# Task 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=False,
    task_track_started=True,
    task_time_limit=600,
    result_expires=3600,
    worker_max_tasks_per_child=10,
    worker_pool='solo',
)

if __name__ == "__main__":
    logger.info("AI-Worker Celery App initialized.")
    
    # 모델 Preload (첫 요청 지연 방지)
    try:
        from tasks.stt import load_models as load_stt
        from tasks.resume_embedding import load_embedding_model
        
        logger.info("Preloading models...")
        load_stt()
        load_embedding_model()
        logger.info("Models preloaded successfully.")
    except Exception as e:
        logger.warning(f"Model preload failed: {e}")

    app.start()