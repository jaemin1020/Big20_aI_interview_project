from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "ai_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# [중요] AI 워커와 동일한 라우팅 규칙 적용 (Producer-Side Routing)
# Celery는 send_task 시점에 Producer의 task_routes 설정을 가장 먼저 따릅니다.
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=False,
    task_default_queue='cpu_queue',
    task_routes={
        # GPU 사용 태스크 (질문 생성, 임베딩, EXAONE 기반 작업)
        'tasks.question_generation.*': {'queue': 'gpu_queue'},
        'tasks.question_generator.*': {'queue': 'gpu_queue'},
        'tasks.resume_pipeline.generate_embeddings': {'queue': 'gpu_queue'},
        'tasks.resume_embedding.*': {'queue': 'gpu_queue'},
        'tasks.evaluator.generate_final_report': {'queue': 'gpu_queue'},
        'tasks.evaluator.analyze_answer': {'queue': 'gpu_queue'},
        'tasks.evaluator.finalize_report_task': {'queue': 'gpu_queue'},
        
        # CPU 사용 태스크 (파싱, STT, TTS, 비전)
        'tasks.resume_pipeline.parse_pdf': {'queue': 'cpu_queue'},
        'tasks.stt.*': {'queue': 'cpu_queue'},
        'tasks.evaluator.*': {'queue': 'cpu_queue'},
        'tasks.vision.*': {'queue': 'cpu_queue'},
        'tasks.resume_parser.*': {'queue': 'cpu_queue'},
        'tasks.tts.*': {'queue': 'cpu_queue'},
    }
)
