import logging
import os
import sys
import multiprocessing

# 0. 경로 우선순위 조정 (중요)
# ai-worker 루트가 backend-core보다 먼저 오도록 강제 (utils 폴더 충돌 방지)
app_root = "/app" if os.path.exists("/app") else os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(app_root, "..", "backend-core"))

# 우선 다 지우고 새로 추가 (순서 보장)
for p in [app_root, backend_root]:
    while p in sys.path: sys.path.remove(p)

sys.path.insert(0, backend_root) # backend가 2순위
sys.path.insert(0, app_root)     # app_root가 최종 1순위 (tasks, config 등이 위치)

# [추가] config 폴더가 있는 위치를 명시적으로 보장
config_parent = os.path.dirname(os.path.abspath(__file__))
if config_parent not in sys.path:
    sys.path.insert(0, config_parent)

from celery import Celery

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
        'tasks.question_generator', 
        'tasks.resume_parser', 
        'tasks.resume_embedding',
        'tasks.stt',
        'tasks.tts'
    ]
)

# 3. 성능 최적화 및 큐 라우팅 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=False,
    task_track_started=True,
    task_time_limit=600,
    result_expires=3600,
    worker_max_tasks_per_child=50, # 메모리 관리 효율화
    # worker_pool='solo' 제거 (CPU/GPU 워커가 각각 다른 풀을 사용하도록 docker-compose에서 결정)
    
    # [큐 라우팅] 역할별 전용 일꾼 시스템 구축
    task_default_queue='cpu_queue',
    task_routes={
        # GPU 사용 태스크 (질문 생성, 임베딩, STT, 리포트)
        'tasks.resume_pipeline.*': {'queue': 'gpu_queue'},
        'tasks.question_generation.*': {'queue': 'gpu_queue'},
        'tasks.question_generator.*': {'queue': 'gpu_queue'},
        'tasks.resume_embedding.*': {'queue': 'gpu_queue'},
        'tasks.evaluator.generate_final_report': {'queue': 'gpu_queue'},
        'tasks.evaluator.analyze_answer': {'queue': 'gpu_queue'},  # EXAONE LLM 필요 → GPU 워커 필수
        'tasks.stt.*': {'queue': 'cpu_queue'},
        
        # CPU 사용 태스크 (비전, 파싱, TTS, 나머지 evaluator)
        'tasks.evaluator.*': {'queue': 'cpu_queue'},  # analyze_answer, generate_final_report 제외한 나머지
        'tasks.vision.*': {'queue': 'cpu_queue'},
        'tasks.resume_parser.*': {'queue': 'cpu_queue'},
        'tasks.tts.*': {'queue': 'cpu_queue'},
    }
)

if __name__ == "__main__":
    logger.info("AI-Worker Celery App initialized.")
    
    # 모델 Preload (첫 요청 지연 방지)
    try:
        from tasks.stt import load_stt_model
        from tasks.resume_embedding import load_embedding_model
        
        logger.info("Preloading models...")
        load_stt_model()
        load_embedding_model()
        logger.info("Models preloaded successfully.")
    except Exception as e:
        logger.warning(f"Model preload failed: {e}")

    app.start()