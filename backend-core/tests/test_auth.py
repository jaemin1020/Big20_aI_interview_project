"""
Authentication Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_user_registration_success(client: TestClient, test_user_data):
    """Test successful user registration"""
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]


def test_user_registration_duplicate_email(client: TestClient, test_user_data):
    """Test registration with duplicate email"""
    # First registration
    client.post("/auth/register", json=test_user_data)
    
    # Second registration with same email
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_user_registration_invalid_email(client: TestClient, test_user_data):
    """Test registration with invalid email"""
    invalid_data = test_user_data.copy()
    invalid_data["email"] = "invalid-email"
    
    response = client.post("/auth/register", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_user_login_success(client: TestClient, test_user_data):
    """Test successful login"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],  # Backend uses email as username
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_user_login_wrong_password(client: TestClient, test_user_data):
    """Test login with wrong password"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login with wrong password
    login_data = {
        "username": test_user_data["email"],
        "password": "WrongPassword123!"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401


def test_user_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "SomePassword123!"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401


def test_get_current_user(client: TestClient, test_user_data):
    """Test getting current user info"""
    # Register and login
    client.post("/auth/register", json=test_user_data)
    login_response = client.post("/auth/login", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without token"""
    response = client.get("/users/me")
    assert response.status_code == 401
