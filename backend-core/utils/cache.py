"""
캐싱 유틸리티
"""
from functools import wraps
from typing import Callable, Any, Optional
import time
import hashlib
import json
import logging

logger = logging.getLogger("CacheUtils")


class SimpleCache:
    """간단한 인메모리 캐시"""
    
    def __init__(self, ttl: int = 3600):
        """
        Args:
            ttl: Time To Live (초)
        """
        self.cache = {}
        self.ttl = ttl
    
    def _is_expired(self, timestamp: float) -> bool:
        """캐시 만료 확인"""
        return time.time() - timestamp > self.ttl
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if not self._is_expired(timestamp):
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                logger.debug(f"Cache expired: {key}")
                del self.cache[key]
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        self.cache[key] = (value, time.time())
        logger.debug(f"Cache set: {key}")
    
    def delete(self, key: str):
        """캐시에서 값 삭제"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """캐시 전체 삭제"""
        self.cache.clear()
        logger.debug("Cache cleared")
    
    def size(self) -> int:
        """캐시 크기"""
        return len(self.cache)


# 전역 캐시 인스턴스
_global_cache = SimpleCache(ttl=3600)


def cache(ttl: int = 3600, key_prefix: str = ""):
    """
    함수 결과 캐싱 데코레이터
    
    Args:
        ttl: Time To Live (초)
        key_prefix: 캐시 키 접두사
        
    Example:
        @cache(ttl=300)
        def get_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # 캐시에서 조회
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 캐시에 저장
            _global_cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str = "") -> str:
    """
    캐시 키 생성
    
    Args:
        func: 함수
        args: 위치 인자
        kwargs: 키워드 인자
        prefix: 접두사
        
    Returns:
        str: 캐시 키
    """
    # 함수명
    func_name = f"{func.__module__}.{func.__name__}"
    
    # 인자를 JSON으로 직렬화
    try:
        args_str = json.dumps(args, sort_keys=True, default=str)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
    except (TypeError, ValueError):
        # 직렬화 실패 시 str() 사용
        args_str = str(args)
        kwargs_str = str(kwargs)
    
    # 해시 생성
    key_data = f"{prefix}:{func_name}:{args_str}:{kwargs_str}"
    cache_key = hashlib.md5(key_data.encode()).hexdigest()
    
    return cache_key


def invalidate_cache(pattern: str = None):
    """
    캐시 무효화
    
    Args:
        pattern: 패턴 (None이면 전체 삭제)
    """
    if pattern is None:
        _global_cache.clear()
    else:
        # 패턴 매칭 삭제 (간단한 구현)
        keys_to_delete = [
            key for key in _global_cache.cache.keys()
            if pattern in key
        ]
        for key in keys_to_delete:
            _global_cache.delete(key)


def get_cache_stats() -> dict:
    """
    캐시 통계
    
    Returns:
        dict: 캐시 통계
    """
    return {
        "size": _global_cache.size(),
        "ttl": _global_cache.ttl
    }


# 사용 예시
if __name__ == "__main__":
    # 간단한 캐싱
    @cache(ttl=60)
    def expensive_function(x: int, y: int) -> int:
        print(f"Computing {x} + {y}...")
        time.sleep(1)  # 시뮬레이션
        return x + y
    
    # 첫 호출 (캐시 미스)
    result1 = expensive_function(1, 2)  # "Computing 1 + 2..." 출력
    print(f"Result: {result1}")
    
    # 두 번째 호출 (캐시 히트)
    result2 = expensive_function(1, 2)  # 즉시 반환
    print(f"Result: {result2}")
    
    # 캐시 통계
    print(f"Cache stats: {get_cache_stats()}")
    
    # 캐시 무효화
    invalidate_cache()
    print(f"Cache cleared. Size: {get_cache_stats()['size']}")
