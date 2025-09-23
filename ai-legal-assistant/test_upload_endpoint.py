#!/usr/bin/env python3
"""
Test the upload endpoint directly
"""

import requests
import json

def test_upload_endpoint():
    """Test the Supabase upload endpoint"""
    
    # First, login to get a token
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }
    
    print("🔐 Logging in...")
    login_response = requests.post("http://localhost:8000/api/auth/login", data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login successful")
    
    # Test the Supabase upload endpoint
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    upload_data = {
        "filename": "test-document.txt",
        "original_filename": "test-document.txt",
        "file_path": "test-user/test-document.txt",
        "file_url": "https://example.com/test-document.txt",
        "file_size": 100,
        "mime_type": "text/plain",
        "title": "Test Document",
        "document_type": "contract",
        "description": "Test upload",
        "supabase_path": "test-user/test-document.txt"
    }
    
    print("📤 Testing Supabase upload endpoint...")
    upload_response = requests.post(
        "http://localhost:8000/api/upload/supabase",
        headers=headers,
        json=upload_data
    )
    
    print(f"Status Code: {upload_response.status_code}")
    print(f"Response: {upload_response.text}")
    
    if upload_response.status_code == 201:
        print("✅ Upload endpoint working!")
    else:
        print("❌ Upload endpoint failed!")

if __name__ == "__main__":
    test_upload_endpoint()
