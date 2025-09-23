#!/usr/bin/env python3
"""
Test API endpoints directly
"""

import requests
import json

def test_api():
    """Test API endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    print("Testing API endpoints...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"✓ Server is running (status: {response.status_code})")
    except Exception as e:
        print(f"✗ Server not running: {e}")
        return
    
    # Test 2: Register a new user
    register_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "newpass123",
        "full_name": "New User"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"✓ Registration: {response.status_code}")
        if response.status_code == 201:
            print("✓ New user registered successfully")
        elif response.status_code == 400:
            print("ℹ User already exists (expected)")
        else:
            print(f"✗ Registration failed: {response.text}")
    except Exception as e:
        print(f"✗ Registration error: {e}")
    
    # Test 3: Login with new user
    login_data = {
        "username": "newuser@example.com",
        "password": "newpass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", data=login_data)
        print(f"✓ Login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Login successful! Token: {data.get('access_token', 'N/A')[:20]}...")
        else:
            print(f"✗ Login failed: {response.text}")
    except Exception as e:
        print(f"✗ Login error: {e}")
    
    # Test 4: Login with existing user
    existing_login_data = {
        "username": "test@example.com",
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", data=existing_login_data)
        print(f"✓ Existing user login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Existing user login successful! Token: {data.get('access_token', 'N/A')[:20]}...")
        else:
            print(f"✗ Existing user login failed: {response.text}")
    except Exception as e:
        print(f"✗ Existing user login error: {e}")

if __name__ == "__main__":
    test_api()
