"""
로깅 설정
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(
    name: str = "AI-Interview",
    level: str = "INFO",
    log_dir: str = "./logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    로깅 설정
    
    Args:
        name: 로거 이름
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 로그 디렉토리
        max_bytes: 최대 파일 크기
        backup_count: 백업 파일 개수
        
    Returns:
        logging.Logger: 설정된 로거
    """
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷터 생성
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (로그 디렉토리가 있는 경우)
    if log_dir:
        # 로그 디렉토리 생성
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 일반 로그 파일
        log_file = log_path / f"{name.lower()}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 에러 로그 파일 (ERROR 이상만)
        error_log_file = log_path / f"{name.lower()}_error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기 (이미 설정된 경우)
    
    Args:
        name: 로거 이름
        
    Returns:
        logging.Logger: 로거
    """
    return logging.getLogger(name)


class StructuredLogger:
    """구조화된 로깅을 위한 래퍼 클래스"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log(self, level: str, message: str, **kwargs):
        """
        구조화된 로그 출력
        
        Args:
            level: 로그 레벨
            message: 메시지
            **kwargs: 추가 컨텍스트
        """
        # 추가 컨텍스트를 문자열로 변환
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {context}" if context else message
        
        log_method = getattr(self.logger, level.lower())
        log_method(full_message)
    
    def info(self, message: str, **kwargs):
        """INFO 레벨 로그"""
        self.log("INFO", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """DEBUG 레벨 로그"""
        self.log("DEBUG", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """WARNING 레벨 로그"""
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ERROR 레벨 로그"""
        self.log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """CRITICAL 레벨 로그"""
        self.log("CRITICAL", message, **kwargs)


# 사용 예시
if __name__ == "__main__":
    # 기본 로거 설정
    logger = setup_logging(
        name="TestLogger",
        level="DEBUG",
        log_dir="./logs"
    )
    
    # 일반 로깅
    logger.info("서버 시작됨")
    logger.debug("디버그 메시지")
    logger.warning("경고 메시지")
    logger.error("에러 발생")
    
    # 구조화된 로깅
    structured_logger = StructuredLogger(logger)
    structured_logger.info(
        "Resume 파싱 완료",
        resume_id=123,
        file_size=245678,
        processing_time=2.5
    )
    # 출력: Resume 파싱 완료 | resume_id=123 | file_size=245678 | processing_time=2.5
