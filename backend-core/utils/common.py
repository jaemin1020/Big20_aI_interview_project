"""
공통 유틸리티 함수
"""
from typing import Optional, Dict, Any
import re
from datetime import datetime


def clean_text(text: str) -> str:
    """
    텍스트 정제
    
    Args:
        text: 원본 텍스트
        
    Returns:
        str: 정제된 텍스트
    """
    if not text:
        return ""
    
    # 여러 개의 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    
    # 여러 개의 줄바꿈을 최대 2개로
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    텍스트 자르기
    
    Args:
        text: 원본 텍스트
        max_length: 최대 길이
        suffix: 접미사
        
    Returns:
        str: 잘린 텍스트
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length] + suffix


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """
    안전한 딕셔너리 값 가져오기 (중첩 지원)
    
    Args:
        data: 딕셔너리
        *keys: 키 경로
        default: 기본값
        
    Returns:
        값 또는 기본값
        
    Example:
        safe_get({"a": {"b": {"c": 1}}}, "a", "b", "c")  # 1
        safe_get({"a": {"b": {}}}, "a", "b", "c", default=0)  # 0
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, IndexError):
        return default


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    datetime 포맷팅
    
    Args:
        dt: datetime 객체
        format_str: 포맷 문자열
        
    Returns:
        str: 포맷팅된 문자열
    """
    if not dt:
        return ""
    
    return dt.strftime(format_str)


def calculate_percentage(value: float, total: float, decimals: int = 2) -> float:
    """
    퍼센트 계산
    
    Args:
        value: 값
        total: 전체
        decimals: 소수점 자릿수
        
    Returns:
        float: 퍼센트
    """
    if total == 0:
        return 0.0
    
    percentage = (value / total) * 100
    return round(percentage, decimals)


def validate_email(email: str) -> bool:
    """
    이메일 유효성 검증
    
    Args:
        email: 이메일 주소
        
    Returns:
        bool: 유효 여부
    """
    if not email or len(email) > 255:
        return False
        
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """
    아이디 유효성 검증 (최대 12글자)
    
    Args:
        username: 사용자 아이디
        
    Returns:
        bool: 유효 여부
    """
    if not username:
        return False
        
    # 길이 체크 (4~12자 권장, 요구사항은 최대 12자)
    if len(username) < 4 or len(username) > 12:
        return False
        
    # 영문 소문자, 숫자, 밑줄(_)만 허용하는 정규식
    pattern = r'^[a-z0-9_]+$'
    return bool(re.match(pattern, username))


def validate_phone(phone: str) -> bool:
    """
    전화번호 유효성 검증 (한국)
    
    Args:
        phone: 전화번호
        
    Returns:
        bool: 유효 여부
    """
    # 010-1234-5678, 01012345678, +82-10-1234-5678 등 지원
    pattern = r'^(\+82-?)?0?1[0-9]-?\d{3,4}-?\d{4}$'
    return bool(re.match(pattern, phone.replace(' ', '')))


def extract_keywords(text: str, min_length: int = 2) -> list:
    """
    텍스트에서 키워드 추출 (간단한 버전)
    
    Args:
        text: 텍스트
        min_length: 최소 길이
        
    Returns:
        list: 키워드 리스트
    """
    # 한글, 영문, 숫자만 추출
    words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
    
    # 최소 길이 필터링 및 중복 제거
    keywords = list(set([w for w in words if len(w) >= min_length]))
    
    return sorted(keywords)


def merge_dicts(*dicts: Dict) -> Dict:
    """
    여러 딕셔너리 병합
    
    Args:
        *dicts: 딕셔너리들
        
    Returns:
        dict: 병합된 딕셔너리
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    리스트를 청크로 나누기
    
    Args:
        lst: 리스트
        chunk_size: 청크 크기
        
    Returns:
        list: 청크 리스트
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


# 사용 예시
if __name__ == "__main__":
    # 텍스트 정제
    text = "안녕하세요   \n\n\n\n  반갑습니다"
    print(clean_text(text))  # "안녕하세요 반갑습니다"
    
    # 안전한 딕셔너리 접근
    data = {"user": {"profile": {"name": "홍길동"}}}
    print(safe_get(data, "user", "profile", "name"))  # "홍길동"
    print(safe_get(data, "user", "profile", "age", default=0))  # 0
    
    # 이메일 검증
    print(validate_email("test@example.com"))  # True
    print(validate_email("invalid-email"))  # False
