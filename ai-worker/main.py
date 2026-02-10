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
app = Celery(
    "ai_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=[
        'tasks.evaluator', 
        'tasks.vision', 
        'tasks.question_generation', 
        'tasks.parse_resume', 
        'tasks.save_structured',
        'tasks.chunking',
        'tasks.embedding',
        'tasks.pgvector_store',
        'tasks.rag_retrieval',
        'tasks.resume_pipeline',
        'tasks.stt'
    ]
)

# 3. 성능 최적화 및 큐 라우팅 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    worker_max_tasks_per_child=10, # 메모리 누수 방지 (64GB 효율 관리)
    worker_pool='solo',  # CUDA 호환성을 위해 solo pool 사용
    
    # [큐 라우팅] 역할별 전용 일꾼 시스템 구축
    task_default_queue='cpu_queue',
    task_routes={
        # GPU 사용 태스크 (질문 생성, 임베딩)
        'tasks.question_generation.*': {'queue': 'gpu_queue'},
        'tasks.embedding.*': {'queue': 'gpu_queue'},
        'tasks.resume_pipeline.*': {'queue': 'gpu_queue'},
        
        # CPU 사용 태스크 (답변 분석, STT, 비전, 기타)
        'tasks.evaluator.*': {'queue': 'cpu_queue'},
        'tasks.stt.*': {'queue': 'cpu_queue'},
        'tasks.vision.*': {'queue': 'cpu_queue'},
        'tasks.parse_resume.*': {'queue': 'cpu_queue'},
        'tasks.save_structured.*': {'queue': 'cpu_queue'},
        'tasks.chunking.*': {'queue': 'cpu_queue'},
    }
)

if __name__ == "__main__":
    logger.info("AI-Worker Celery App initialized.")
    app.start()