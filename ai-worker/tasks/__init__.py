
# AI-Worker Tasks Package
# 🚨 Circular/Heavy Input avoidance
# Modules are imported lazily or individually by callers to avoid missing dependency errors (like deepface) in local environments.

__all__ = [
    'analyze_answer', 
    'analyze_emotion', 
    'generate_next_question_task',
    'parse_resume_pdf',
    'generate_resume_embeddings',
    'recognize_audio_task',
    'synthesize_task'
]