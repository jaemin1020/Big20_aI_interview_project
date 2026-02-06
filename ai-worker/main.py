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
# include=['tasks.evaluator', 'tasks.vision']를 통해 무거운 import를 분산함
app = Celery(
    "ai_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=['tasks.evaluator', 'tasks.vision', 'tasks.question_generator', 'tasks.resume_parser', 'tasks.answer_collector', 'tasks.search_helper']
)

# 3. 성능 최적화 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    worker_max_tasks_per_child=10, # 메모리 누수 방지 (64GB 효율 관리)
    worker_pool='solo',  # CUDA 호환성을 위해 solo pool 사용
)

if __name__ == "__main__":
    logger.info("AI-Worker Celery App initialized.")
    app.start()