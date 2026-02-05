"""
커스텀 예외 클래스
"""


class BaseAPIException(Exception):
    """기본 API 예외"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# Resume 관련 예외
class ResumeNotFoundError(BaseAPIException):
    """이력서를 찾을 수 없음"""
    def __init__(self, resume_id: int):
        super().__init__(
            message=f"Resume {resume_id}를 찾을 수 없습니다.",
            status_code=404
        )


class ResumeProcessingError(BaseAPIException):
    """이력서 처리 오류"""
    def __init__(self, resume_id: int, detail: str = ""):
        super().__init__(
            message=f"Resume {resume_id} 처리 중 오류 발생: {detail}",
            status_code=500
        )


class ResumeUploadError(BaseAPIException):
    """이력서 업로드 오류"""
    def __init__(self, detail: str):
        super().__init__(
            message=f"이력서 업로드 실패: {detail}",
            status_code=400
        )


# Interview 관련 예외
class InterviewNotFoundError(BaseAPIException):
    """면접을 찾을 수 없음"""
    def __init__(self, interview_id: int):
        super().__init__(
            message=f"Interview {interview_id}를 찾을 수 없습니다.",
            status_code=404
        )


class InterviewCreationError(BaseAPIException):
    """면접 생성 오류"""
    def __init__(self, detail: str):
        super().__init__(
            message=f"면접 생성 실패: {detail}",
            status_code=400
        )


# Question 관련 예외
class QuestionGenerationError(BaseAPIException):
    """질문 생성 오류"""
    def __init__(self, detail: str):
        super().__init__(
            message=f"질문 생성 실패: {detail}",
            status_code=500
        )


class QuestionNotFoundError(BaseAPIException):
    """질문을 찾을 수 없음"""
    def __init__(self, question_id: int):
        super().__init__(
            message=f"Question {question_id}를 찾을 수 없습니다.",
            status_code=404
        )


# Company 관련 예외
class CompanyNotFoundError(BaseAPIException):
    """회사를 찾을 수 없음"""
    def __init__(self, company_id: str):
        super().__init__(
            message=f"Company {company_id}를 찾을 수 없습니다.",
            status_code=404
        )


# User 관련 예외
class UserNotFoundError(BaseAPIException):
    """사용자를 찾을 수 없음"""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User {user_id}를 찾을 수 없습니다.",
            status_code=404
        )


class UnauthorizedError(BaseAPIException):
    """권한 없음"""
    def __init__(self, detail: str = "권한이 없습니다."):
        super().__init__(
            message=detail,
            status_code=403
        )


class AuthenticationError(BaseAPIException):
    """인증 실패"""
    def __init__(self, detail: str = "인증에 실패했습니다."):
        super().__init__(
            message=detail,
            status_code=401
        )


# Validation 관련 예외
class ValidationError(BaseAPIException):
    """유효성 검증 오류"""
    def __init__(self, field: str, detail: str):
        super().__init__(
            message=f"{field} 유효성 검증 실패: {detail}",
            status_code=400
        )


class FileSizeExceededError(BaseAPIException):
    """파일 크기 초과"""
    def __init__(self, max_size: int):
        super().__init__(
            message=f"파일 크기가 {max_size}MB를 초과했습니다.",
            status_code=400
        )


class InvalidFileTypeError(BaseAPIException):
    """잘못된 파일 형식"""
    def __init__(self, allowed_types: list):
        super().__init__(
            message=f"허용된 파일 형식: {', '.join(allowed_types)}",
            status_code=400
        )


# Database 관련 예외
class DatabaseError(BaseAPIException):
    """데이터베이스 오류"""
    def __init__(self, detail: str):
        super().__init__(
            message=f"데이터베이스 오류: {detail}",
            status_code=500
        )


class DuplicateEntryError(BaseAPIException):
    """중복 항목"""
    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"{field} '{value}'가 이미 존재합니다.",
            status_code=409
        )


# External Service 관련 예외
class ExternalServiceError(BaseAPIException):
    """외부 서비스 오류"""
    def __init__(self, service_name: str, detail: str):
        super().__init__(
            message=f"{service_name} 서비스 오류: {detail}",
            status_code=503
        )


class LLMServiceError(ExternalServiceError):
    """LLM 서비스 오류"""
    def __init__(self, detail: str):
        super().__init__(
            service_name="LLM",
            detail=detail
        )


class STTServiceError(ExternalServiceError):
    """STT 서비스 오류"""
    def __init__(self, detail: str):
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
