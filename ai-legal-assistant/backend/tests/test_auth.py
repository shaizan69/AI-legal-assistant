"""
Authentication tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core.auth import get_password_hash
from app.models.user import User

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }

def test_register_user(client, test_user):
    """Test user registration"""
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]
    assert "id" in data

def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email"""
    # First registration
    client.post("/api/auth/register", json=test_user)
    
    # Second registration with same email
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_user(client, test_user):
    """Test user login"""
    # Register user first
    client.post("/api/auth/register", json=test_user)
    
    # Login
    response = client.post("/api/auth/login", data={
        "username": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post("/api/auth/login", data={
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_current_user(client, test_user):
    """Test getting current user info"""
    # Register and login
    client.post("/api/auth/register", json=test_user)
    login_response = client.post("/api/auth/login", data={
        "username": test_user["email"],
        "password": test_user["password"]
    })
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]

def test_get_current_user_unauthorized(client):
    """Test getting current user without token"""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
