#!/usr/bin/env python3
"""
Test the upload API to ensure it's working properly
"""

import requests
import json
import os

def test_upload_api():
    """Test the upload API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Upload API...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ Backend server is running")
        else:
            print("❌ Backend server not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test 2: Test Supabase upload endpoint
    print("\n📤 Testing Supabase upload endpoint...")
    
    # Create a test document data
    test_data = {
        "filename": "test-document.pdf",
        "original_filename": "test-document.pdf",
        "file_path": "test/1234567890_test-document.pdf",
        "file_url": "https://mnadbvirdkzgrlzgbrai.supabase.co/storage/v1/object/public/legal-documents/test/1234567890_test-document.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "title": "Test Document",
        "document_type": "contract",
        "description": "This is a test document",
        "supabase_path": "test/1234567890_test-document.pdf"
    }
    
    try:
        # Note: This will fail without authentication, but we can check if the endpoint exists
        response = requests.post(f"{base_url}/api/upload/supabase", json=test_data)
        
        if response.status_code == 401:
            print("✅ Supabase upload endpoint exists (authentication required)")
        elif response.status_code == 200:
            print("✅ Supabase upload endpoint working")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing upload endpoint: {e}")
    
    # Test 3: Test regular upload endpoint
    print("\n📤 Testing regular upload endpoint...")
    
    try:
        response = requests.get(f"{base_url}/api/upload/")
        
        if response.status_code == 401:
            print("✅ Regular upload endpoint exists (authentication required)")
        elif response.status_code == 200:
            print("✅ Regular upload endpoint working")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing upload endpoint: {e}")
    
    print("\n🎉 API test completed!")
    print("\n📋 Next steps:")
    print("1. Go to http://localhost:3000")
    print("2. Register/Login to your account")
    print("3. Go to http://localhost:3000/upload")
    print("4. Try uploading a file!")
    
    return True

if __name__ == "__main__":
    test_upload_api()
