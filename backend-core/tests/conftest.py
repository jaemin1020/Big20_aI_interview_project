"""
Backend Core Tests Configuration
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from main import app
from database import get_session


# Test Database Setup (In-Memory SQLite)
@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with dependency override"""
    def get_session_override():
        """설명:
            FastAPI 의존성 주입을 위한 테스트용 세션 오버라이드 함수.

        Returns:
            Session: 테스트 전용 DB 세션.

        생성자: ejm
        생성일자: 2026-02-04
        """
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_interview_data():
    """Sample interview data for testing"""
    return {
        "candidate_name": "홍길동",
        "position": "Backend Developer",
        "company_id": "KAKAO"
    }
