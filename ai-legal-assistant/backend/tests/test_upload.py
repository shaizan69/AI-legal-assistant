"""
Document upload tests
"""

import pytest
import io
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
def auth_headers(client):
    """Create a test user and return auth headers"""
    # Register user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

def test_upload_document(client, auth_headers):
    """Test document upload"""
    # Create a test file
    test_file = io.BytesIO(b"This is a test document content.")
    test_file.name = "test.txt"
    
    response = client.post(
        "/api/upload/",
        files={"file": test_file},
        data={"title": "Test Document"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] is not None
    assert data["title"] == "Test Document"
    assert data["owner_id"] is not None

def test_upload_document_unauthorized(client):
    """Test upload without authentication"""
    test_file = io.BytesIO(b"This is a test document content.")
    test_file.name = "test.txt"
    
    response = client.post(
        "/api/upload/",
        files={"file": test_file},
        data={"title": "Test Document"}
    )
    
    assert response.status_code == 401

def test_upload_invalid_file_type(client, auth_headers):
    """Test upload with invalid file type"""
    test_file = io.BytesIO(b"This is a test document content.")
    test_file.name = "test.exe"
    
    response = client.post(
        "/api/upload/",
        files={"file": test_file},
        data={"title": "Test Document"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "File type not allowed" in response.json()["detail"]

def test_get_documents(client, auth_headers):
    """Test getting user documents"""
    response = client.get("/api/upload/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert "page" in data

def test_get_document(client, auth_headers):
    """Test getting a specific document"""
    # First upload a document
    test_file = io.BytesIO(b"This is a test document content.")
    test_file.name = "test.txt"
    
    upload_response = client.post(
        "/api/upload/",
        files={"file": test_file},
        data={"title": "Test Document"},
        headers=auth_headers
    )
    
    document_id = upload_response.json()["id"]
    
    # Get the document
    response = client.get(f"/api/upload/{document_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert data["title"] == "Test Document"

def test_delete_document(client, auth_headers):
    """Test deleting a document"""
    # First upload a document
    test_file = io.BytesIO(b"This is a test document content.")
    test_file.name = "test.txt"
    
    upload_response = client.post(
        "/api/upload/",
        files={"file": test_file},
        data={"title": "Test Document"},
        headers=auth_headers
    )
    
    document_id = upload_response.json()["id"]
    
    # Delete the document
    response = client.delete(f"/api/upload/{document_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify document is deleted
    get_response = client.get(f"/api/upload/{document_id}", headers=auth_headers)
    assert get_response.status_code == 404
