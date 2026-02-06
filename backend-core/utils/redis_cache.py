"""
Redis 기반 캐싱 유틸리티 (기존 cache.py 확장)
"""
import json
import logging
from typing import Optional, Any
import redis
import os

logger = logging.getLogger("RedisCache")

# Redis 연결
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info(f"✅ Redis connected: {REDIS_URL}")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    redis_client = None

# 캐시 TTL 설정 (초)
CACHE_TTL = {
    "question": 3600,      # 1시간
    "company": 7200,       # 2시간
    "user": 1800,          # 30분
    "interview": 600,      # 10분
    "report": 1800,        # 30분
}


def cache_key(prefix: str, *args) -> str:
    """캐시 키 생성"""
    return f"{prefix}:{':'.join(map(str, args))}"


def get_cached(key: str) -> Optional[Any]:
    """Redis에서 캐시 조회"""
    if not redis_client:
        return None
    
    try:
        data = redis_client.get(key)
        if data:
            logger.debug(f"✅ Cache HIT: {key}")
            return json.loads(data)
        logger.debug(f"❌ Cache MISS: {key}")
        return None
    except Exception as e:
        logger.error(f"Cache get error for {key}: {e}")
        return None


def set_cached(key: str, value: Any, ttl: int = 3600) -> bool:
    """Redis에 캐시 저장"""
    if not redis_client:
        return False
    
    try:
        redis_client.setex(key, ttl, json.dumps(value, default=str))
        logger.debug(f"💾 Cache SET: {key} (TTL={ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set error for {key}: {e}")
        return False


def delete_cached(key: str) -> bool:
    """캐시 삭제"""
    if not redis_client:
        return False
    
    try:
        redis_client.delete(key)
        logger.debug(f"🗑️ Cache DELETE: {key}")
        return True
    except Exception as e:
        logger.error(f"Cache delete error for {key}: {e}")
        return False


def invalidate_pattern(pattern: str) -> int:
    """패턴에 맞는 모든 캐시 삭제"""
    if not redis_client:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            count = redis_client.delete(*keys)
            logger.info(f"🗑️ Invalidated {count} cache keys matching '{pattern}'")
            return count
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation error for pattern '{pattern}': {e}")
        return 0


# ==================== 특화 캐싱 함수 ====================

def cache_interview_questions(interview_id: int, questions: list) -> bool:
    """면접 질문 목록 캐싱"""
    key = cache_key("interview_questions", interview_id)
    return set_cached(key, questions, CACHE_TTL["interview"])


def get_cached_interview_questions(interview_id: int) -> Optional[list]:
    """캐시된 면접 질문 목록 조회"""
    key = cache_key("interview_questions", interview_id)
    return get_cached(key)


def cache_company(company_id: int, company_data: dict) -> bool:
    """회사 정보 캐싱"""
    key = cache_key("company", company_id)
    return set_cached(key, company_data, CACHE_TTL["company"])


def get_cached_company(company_id: int) -> Optional[dict]:
    """캐시된 회사 정보 조회"""
    key = cache_key("company", company_id)
    return get_cached(key)


def cache_evaluation_report(interview_id: int, report_data: dict) -> bool:
    """평가 리포트 캐싱"""
    key = cache_key("report", interview_id)
    return set_cached(key, report_data, CACHE_TTL["report"])


def get_cached_evaluation_report(interview_id: int) -> Optional[dict]:
    """캐시된 평가 리포트 조회"""
    key = cache_key("report", interview_id)
    return get_cached(key)


def invalidate_interview_cache(interview_id: int):
    """면접 관련 모든 캐시 무효화"""
    invalidate_pattern(f"interview_questions:{interview_id}*")
    invalidate_pattern(f"report:{interview_id}*")


def get_cache_stats() -> dict:
    """Redis 캐시 통계"""
    if not redis_client:
        return {"status": "disconnected"}
    
    try:
        info = redis_client.info("stats")
        return {
            "status": "connected",
            "total_keys": redis_client.dbsize(),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": round(
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                2
            )
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}
