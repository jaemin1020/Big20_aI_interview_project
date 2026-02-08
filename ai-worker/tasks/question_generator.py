import os
import logging
from celery import shared_task
from typing import Optional, List

# DB 헬퍼 함수 import
from db import (
    get_best_questions_by_position,
    increment_question_usage,
    engine
)
from sqlmodel import Session, select

# EXAONE LLM import
from utils.exaone_llm import get_exaone_llm

logger = logging.getLogger("AI-Worker-QuestionGen")

class QuestionGenerator:
    """
    하이브리드 질문 생성기 (EXAONE-3.5-7.8B-Instruct 사용)
    전략: DB 재활용 (40%) + Few-Shot LLM 생성 (60%)
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        logger.info("Initializing Question Generator with EXAONE model")
        self.llm = get_exaone_llm()
        self._initialized = True
        logger.info("✅ Question Generator Initialized")

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        """
        하이브리드 질문 생성 로직 (이력서 및 회사 정보 기반)
        1. DB에서 검증된 질문 일부 재활용 (Reuse)
        2. 이력서 + 회사 정보로 컨텍스트 구성
        3. 재활용된 질문을 예시(Few-Shot)로 삼아 나머지 질문 생성 (Create)
        
        Args:
            position: 지원 직무
            interview_id: 면접 ID (이력서/회사 정보 조회용)
            count: 생성할 총 질문 수
            reuse_ratio: 재활용 비율 (0.0 ~ 1.0)
        """
        from tools import ResumeTool, CompanyTool
        
        questions = []
        reuse_count = int(count * reuse_ratio)
        generate_count = count - reuse_count
        
        # 1. 컨텍스트 수집 (이력서 + 회사 정보)
        context_parts = []
        
        if interview_id:
            # 이력서 정보
            resume_info = ResumeTool.get_resume_by_interview(interview_id)
            if resume_info.get("has_resume"):
                context_parts.append(ResumeTool.format_for_llm(resume_info))
                logger.info(f"이력서 정보 로드 완료: {resume_info.get('summary', '')[:50]}...")
            
            # 회사 정보
            company_info = CompanyTool.get_company_by_interview(interview_id)
            if company_info.get("has_company"):
                context_parts.append(CompanyTool.format_for_llm(company_info))
                logger.info(f"회사 정보 로드 완료: {company_info.get('name', '')}")
        
        context = "\n\n".join(context_parts) if context_parts else ""
        
        # 2. DB에서 기존 질문 재활용 (Reuse)
        if reuse_count > 0:
            reused = self._reuse_questions_from_db(position, reuse_count)
            questions.extend(reused)
            logger.info(f"✅ DB에서 {len(reused)}개 질문 재활용")
        
        # 3. EXAONE LLM으로 새 질문 생성 (Create with Context)
        if generate_count > 0:
            generated = self.llm.generate_questions(
                position=position,
                context=context,
                examples=questions,  # Few-shot 예시로 재활용된 질문 사용
                count=generate_count
            )
            questions.extend(generated)
            logger.info(f"✅ EXAONE으로 {len(generated)}개 질문 생성 (컨텍스트 포함)")
        
        return questions[:count]  # 정확히 count개만 반환
    
    def _reuse_questions_from_db(self, position: str, count: int):
        """DB에서 검증된 질문 가져오기"""
        
        try:
            db_questions = get_best_questions_by_position(position, limit=count)
            
            # 재활용 시 사용량 증가
            for q in db_questions:
                try:
                    increment_question_usage(q.id)
                except Exception as e:
                    logger.warning(f"Question {q.id} 사용량 증가 실패: {e}")
            
            return [q.content for q in db_questions]
        except Exception as e:
            logger.warning(f"DB 질문 조회 실패: {e}. 빈 리스트 반환")
            return []

@shared_task(name="tasks.question_generator.generate_questions")
def generate_questions_task(position: str, interview_id: int = None, count: int = 5):
    try:
        generator = QuestionGenerator()
        return generator.generate_questions(position, interview_id, count)
    except Exception as e:
        logger.error(f"Task Error: {e}")
        return []

# Eager Initialization: Worker 시작 시 모델 미리 로드
try:
    logger.info("🔥 Pre-loading Question Generator with EXAONE...")
    _warmup_generator = QuestionGenerator()
    logger.info("✅ Question Generator ready for requests")
except Exception as e:
    logger.warning(f"⚠️ Failed to pre-load model (will load on first request): {e}")
