"""
커스텀 예외 클래스
"""


class BaseAPIException(Exception):
    """설명:
        기본 API 예외 클래스

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, message: str, status_code: int = 500):
        """설명:
            API 예외 기본 초기화메서드.

        Args:
            message (str): 예외 내용 메시지.
            status_code (int): HTTP 상태 코드 (default: 500).

        생성자: ejm
        생성일자: 2026-02-06
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# Resume 관련 예외
class ResumeNotFoundError(BaseAPIException):
    """설명:
        이력서를 찾을 수 없음

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, resume_id: int):
        """설명:
            이력서를 찾을 수 없음 예외 초기화.

        Args:
            resume_id (int): 조회 실패한 이력서 ID.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"Resume {resume_id}를 찾을 수 없습니다.",
            status_code=404
        )


class ResumeProcessingError(BaseAPIException):
    """설명:
        이력서 처리 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, resume_id: int, detail: str = ""):
        """설명:
            이력서 처리 오류 예외 초기화.

        Args:
            resume_id (int): 처리 실패한 이력서 ID.
            detail (str): 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"Resume {resume_id} 처리 중 오류 발생: {detail}",
            status_code=500
        )


class ResumeUploadError(BaseAPIException):
    """설명:
        이력서 업로드 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str):
        """설명:
            이력서 업로드 오류 예외 초기화.

        Args:
            detail (str): 업로드 실패 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"이력서 업로드 실패: {detail}",
            status_code=400
        )


# Interview 관련 예외
class InterviewNotFoundError(BaseAPIException):
    """설명:
        면접을 찾을 수 없음

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, interview_id: int):
        """설명:
            면접 세션을 찾을 수 없음 예외 초기화.

        Args:
            interview_id (int): 조회 실패한 면접 ID.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"Interview {interview_id}를 찾을 수 없습니다.",
            status_code=404
        )


class InterviewCreationError(BaseAPIException):
    """설명:
        면접 생성 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str):
        """설명:
            면접 세션 생성 오류 예외 초기화.

        Args:
            detail (str): 생성 실패 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"면접 생성 실패: {detail}",
            status_code=400
        )


# Question 관련 예외
class QuestionGenerationError(BaseAPIException):
    """설명:
        질문 생성 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str):
        """설명:
            질문 생성 오류 예외 초기화.

        Args:
            detail (str): 생성 실패 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"질문 생성 실패: {detail}",
            status_code=500
        )


class QuestionNotFoundError(BaseAPIException):
    """설명:
        질문을 찾을 수 없음

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, question_id: int):
        """설명:
            질문을 찾을 수 없음 예외 초기화.

        Args:
            question_id (int): 조회 실패한 질문 ID.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"Question {question_id}를 찾을 수 없습니다.",
            status_code=404
        )


# Company 관련 예외
class CompanyNotFoundError(BaseAPIException):
    """설명:
        회사를 찾을 수 없음

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, company_id: str):
        """설명:
            회사를 찾을 수 없음 예외 초기화.

        Args:
            company_id (str): 조회 실패한 회사 ID.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"Company {company_id}를 찾을 수 없습니다.",
            status_code=404
        )


# User 관련 예외
class UserNotFoundError(BaseAPIException):
    """설명:
        사용자를 찾을 수 없음

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, user_id: int):
        """설명:
            사용자를 찾을 수 없음 예외 초기화.

        Args:
            user_id (int): 조회 실패한 사용자 ID.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"User {user_id}를 찾을 수 없습니다.",
            status_code=404
        )


class UnauthorizedError(BaseAPIException):
    """설명:
        권한 없음

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str = "권한이 없습니다."):
        """설명:
            인증되었으나 접근 권한이 없음 예외 초기화.

        Args:
            detail (str): 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=detail,
            status_code=403
        )


class AuthenticationError(BaseAPIException):
    """설명:
        인증 실패

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str = "인증에 실패했습니다."):
        """설명:
            로그인 인증 실패 예외 초기화.

        Args:
            detail (str): 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=detail,
            status_code=401
        )


# Validation 관련 예외
class ValidationError(BaseAPIException):
    """설명:
        유효성 검증 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, field: str, detail: str):
        """설명:
            유효성 검증 실패 예외 초기화.

        Args:
            field (str): 검증 실패한 필드명.
            detail (str): 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"{field} 유효성 검증 실패: {detail}",
            status_code=400
        )


class FileSizeExceededError(BaseAPIException):
    """설명:
        파일 크기 초과

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, max_size: int):
        """설명:
            파일 크기 초과 예외 초기화.

        Args:
            max_size (int): 허용된 최대 파일 크기 (MB).

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"파일 크기가 {max_size}MB를 초과했습니다.",
            status_code=400
        )


class InvalidFileTypeError(BaseAPIException):
    """설명:
        잘못된 파일 형식

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, allowed_types: list):
        """설명:
            허용되지 않는 파일 형식 예외 초기화.

        Args:
            allowed_types (list): 허용된 파일 확장자 목록.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"허용된 파일 형식: {', '.join(allowed_types)}",
            status_code=400
        )


# Database 관련 예외
class DatabaseError(BaseAPIException):
    """설명:
        데이터베이스 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str):
        """설명:
            데이터베이스 오류 예외 초기화.

        Args:
            detail (str): 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"데이터베이스 오류: {detail}",
            status_code=500
        )


class DuplicateEntryError(BaseAPIException):
    """설명:
        중복 항목

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, field: str, value: str):
        """설명:
            중복 데이터 예외 초기화.

        Args:
            field (str): 중복 내용이 발생한 필드명.
            value (str): 중복된 값.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"{field} '{value}'가 이미 존재합니다.",
            status_code=409
        )


# External Service 관련 예외
class ExternalServiceError(BaseAPIException):
    """설명:
        외부 서비스 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, service_name: str, detail: str):
        """설명:
            외부 서비스 오류 예외 초기화.

        Args:
            service_name (str): 오류가 발생한 서비스 이름.
            detail (str): 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            message=f"{service_name} 서비스 오류: {detail}",
            status_code=503
        )


class LLMServiceError(ExternalServiceError):
    """설명:
        LLM 서비스 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str):
        """설명:
            LLM 서비스 오류 예외 초기화.

        Args:
            detail (str): LLM 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            service_name="LLM",
            detail=detail
        )


class STTServiceError(ExternalServiceError):
    """설명:
        STT 서비스 오류

        생성자: ejm
        생성일자: 2026-02-06
    """
    def __init__(self, detail: str):
        """설명:
            STT 서비스 오류 예외 초기화.

        Args:
            detail (str): STT 오류 상세 내용.

        생성자: ejm
        생성일자: 2026-02-06
        """
        super().__init__(
            service_name="STT",
            detail=detail
        )


# 사용 예시
if __name__ == "__main__":

    try:
        raise ResumeNotFoundError(resume_id=123)
    except ResumeNotFoundError as e:
        print(f"Error: {e.message}, Status: {e.status_code}")
    
    try:
        raise ValidationError(field="email", detail="잘못된 이메일 형식")
    except ValidationError as e:
        print(f"Error: {e.message}, Status: {e.status_code}")
