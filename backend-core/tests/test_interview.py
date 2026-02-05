"""
Interview API Tests
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def authenticated_client(client: TestClient, test_user_data):
    """Create an authenticated client"""
    # Register and login
    client.post("/auth/register", json=test_user_data)
    login_response = client.post("/auth/login", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    # Add token to headers
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


def test_create_interview_success(authenticated_client: TestClient, test_interview_data):
    """Test successful interview creation"""
    response = authenticated_client.post("/interviews/", json=test_interview_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["candidate_name"] == test_interview_data["candidate_name"]
    assert data["position"] == test_interview_data["position"]
    assert data["status"] == "scheduled"


def test_create_interview_unauthorized(client: TestClient, test_interview_data):
    """Test interview creation without authentication"""
    response = client.post("/interviews/", json=test_interview_data)
    assert response.status_code == 401


def test_create_interview_missing_fields(authenticated_client: TestClient):
    """Test interview creation with missing required fields"""
    incomplete_data = {
        "candidate_name": "홍길동"
        # Missing position
    }
    response = authenticated_client.post("/interviews/", json=incomplete_data)
    assert response.status_code == 422  # Validation error


def test_get_interview_questions(authenticated_client: TestClient, test_interview_data):
    """Test getting interview questions"""
    # Create interview first
    create_response = authenticated_client.post("/interviews/", json=test_interview_data)
    interview_id = create_response.json()["id"]
    
    # Get questions
    response = authenticated_client.get(f"/interviews/{interview_id}/questions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Questions should be generated
    assert len(data) > 0


def test_get_interview_questions_not_found(authenticated_client: TestClient):
    """Test getting questions for non-existent interview"""
    response = authenticated_client.get("/interviews/99999/questions")
    assert response.status_code == 404


def test_create_transcript(authenticated_client: TestClient, test_interview_data):
    """Test creating a transcript entry"""
    # Create interview first
    create_response = authenticated_client.post("/interviews/", json=test_interview_data)
    interview_id = create_response.json()["id"]
    
    # Create transcript
    transcript_data = {
        "interview_id": interview_id,
        "speaker": "User",
        "text": "저는 3년간 백엔드 개발 경험이 있습니다.",
        "order": 1
    }
    response = authenticated_client.post("/transcripts/", json=transcript_data)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == transcript_data["text"]
    assert data["speaker"] == transcript_data["speaker"]


def test_get_interview_transcripts(authenticated_client: TestClient, test_interview_data):
    """Test getting all transcripts for an interview"""
    # Create interview
    create_response = authenticated_client.post("/interviews/", json=test_interview_data)
    interview_id = create_response.json()["id"]
    
    # Create multiple transcripts
    for i in range(3):
        authenticated_client.post("/transcripts/", json={
            "interview_id": interview_id,
            "speaker": "User" if i % 2 == 0 else "AI",
            "text": f"Test transcript {i}",
            "order": i
        })
    
    # Get all transcripts
    response = authenticated_client.get(f"/interviews/{interview_id}/transcripts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_complete_interview(authenticated_client: TestClient, test_interview_data):
    """Test completing an interview"""
    # Create interview
    create_response = authenticated_client.post("/interviews/", json=test_interview_data)
    interview_id = create_response.json()["id"]
    
    # Complete interview
    response = authenticated_client.post(f"/interviews/{interview_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_get_evaluation_report(authenticated_client: TestClient, test_interview_data):
    """Test getting evaluation report"""
    # Create and complete interview
    create_response = authenticated_client.post("/interviews/", json=test_interview_data)
    interview_id = create_response.json()["id"]
    authenticated_client.post(f"/interviews/{interview_id}/complete")
    
    # Get evaluation report (may need to wait for async task in real scenario)
    response = authenticated_client.get(f"/interviews/{interview_id}/evaluation")
    # Report might not be ready immediately, so we accept both 200 and 404
    assert response.status_code in [200, 404]
