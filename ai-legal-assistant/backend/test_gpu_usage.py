#!/usr/bin/env python3
"""
Test GPU usage with Ollama
"""

import requests
import time
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def test_gpu_usage():
    """Test if GPU is being used by Ollama"""
    print("🔍 TESTING GPU USAGE WITH OLLAMA")
    print("=" * 50)
    
    ollama_url = settings.OLLAMA_URL
    model = settings.LEGAL_MODEL
    
    print(f"Ollama URL: {ollama_url}")
    print(f"Model: {model}")
    
    # Test 1: Check if Ollama is running
    print("\n1. Checking Ollama status...")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("❌ Ollama is not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False
    
    # Test 2: Test GPU usage
    print("\n2. Testing GPU usage...")
    try:
        payload = {
            "model": model,
            "prompt": "What is a contract? Answer briefly.",
            "stream": False,
            "options": {
                "num_gpu": 1,        # Force GPU usage
                "gpu_layers": -1,     # Use all GPU layers
                "low_vram": False,    # Use full VRAM
                "num_ctx": 1024,      # Medium context
                "num_thread": 4,      # More threads
                "num_batch": 4,       # Larger batch
                "use_mmap": True,     # Memory mapping
                "use_mlock": False    # Don't lock memory
            }
        }
        
        print("Sending request with GPU settings...")
        start_time = time.time()
        
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request successful!")
            print(f"   Response time: {response_time:.2f} seconds")
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            print(f"   Model used: {result.get('model', 'Unknown')}")
            
            # Check if GPU was actually used
            if response_time < 5:  # Fast response usually indicates GPU usage
                print("✅ Fast response suggests GPU acceleration is working")
            else:
                print("⚠️ Slow response might indicate CPU usage")
                
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GPU: {e}")
        return False

def test_cpu_vs_gpu():
    """Compare CPU vs GPU performance"""
    print("\n3. Comparing CPU vs GPU performance...")
    
    ollama_url = settings.OLLAMA_URL
    model = settings.LEGAL_MODEL
    
    # Test CPU
    print("Testing CPU mode...")
    cpu_payload = {
        "model": model,
        "prompt": "What is a contract?",
        "stream": False,
        "options": {
            "num_gpu": 0,        # CPU only
            "num_ctx": 512,
            "num_thread": 2,
            "num_batch": 1
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{ollama_url}/api/generate", json=cpu_payload, timeout=60)
        cpu_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ CPU test: {cpu_time:.2f} seconds")
        else:
            print(f"❌ CPU test failed: {response.status_code}")
            cpu_time = None
    except Exception as e:
        print(f"❌ CPU test error: {e}")
        cpu_time = None
    
    # Test GPU
    print("Testing GPU mode...")
    gpu_payload = {
        "model": model,
        "prompt": "What is a contract?",
        "stream": False,
        "options": {
            "num_gpu": 1,        # GPU only
            "gpu_layers": -1,
            "low_vram": False,
            "num_ctx": 1024,
            "num_thread": 4,
            "num_batch": 4
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{ollama_url}/api/generate", json=gpu_payload, timeout=60)
        gpu_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ GPU test: {gpu_time:.2f} seconds")
        else:
            print(f"❌ GPU test failed: {response.status_code}")
            gpu_time = None
    except Exception as e:
        print(f"❌ GPU test error: {e}")
        gpu_time = None
    
    # Compare results
    if cpu_time and gpu_time:
        if gpu_time < cpu_time:
            print(f"✅ GPU is faster! ({gpu_time:.2f}s vs {cpu_time:.2f}s)")
        else:
            print(f"⚠️ CPU is faster ({cpu_time:.2f}s vs {gpu_time:.2f}s) - GPU might not be working")
    else:
        print("⚠️ Could not compare CPU vs GPU performance")

if __name__ == "__main__":
    try:
        success = test_gpu_usage()
        if success:
            test_cpu_vs_gpu()
            print("\n" + "=" * 50)
            print("🎉 GPU TEST COMPLETED!")
            print("Check Task Manager GPU usage during the test")
            print("=" * 50)
        else:
            print("\n❌ GPU test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
