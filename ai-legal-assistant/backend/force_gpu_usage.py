#!/usr/bin/env python3
"""
Force GPU usage for Ollama
"""

import subprocess
import os
import time

def restart_ollama_with_gpu():
    """Restart Ollama with GPU environment variables"""
    print("🔄 RESTARTING OLLAMA WITH GPU FORCE")
    print("=" * 50)
    
    # Set GPU environment variables
    env_vars = {
        'CUDA_VISIBLE_DEVICES': '0',
        'OLLAMA_GPU_LAYERS': '-1',
        'OLLAMA_NUM_GPU': '1',
        'OLLAMA_MODELS': 'D:\\Ollama'
    }
    
    print("Setting environment variables:")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key} = {value}")
    
    # Kill existing Ollama processes
    print("\nStopping existing Ollama processes...")
    try:
        subprocess.run(['taskkill', '/f', '/im', 'ollama.exe'], 
                      capture_output=True, text=True)
        print("✅ Ollama processes stopped")
    except:
        print("ℹ️ No Ollama processes to stop")
    
    # Wait a moment
    time.sleep(2)
    
    # Start Ollama with GPU settings
    print("\nStarting Ollama with GPU settings...")
    try:
        # Start Ollama in background with GPU environment
        process = subprocess.Popen(['ollama', 'serve'], 
                                 env=env_vars,
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
        
        print("✅ Ollama started with GPU settings")
        print(f"   Process ID: {process.pid}")
        
        # Wait for Ollama to start
        time.sleep(5)
        
        # Test if it's running
        import requests
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama is responding")
                return True
            else:
                print("❌ Ollama is not responding")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Ollama: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False

def check_gpu_availability():
    """Check if GPU is available"""
    print("\n🔍 CHECKING GPU AVAILABILITY")
    print("=" * 30)
    
    try:
        # Try to import torch and check CUDA
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA is available")
            print(f"   GPU count: {torch.cuda.device_count()}")
            print(f"   Current device: {torch.cuda.current_device()}")
            print(f"   Device name: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("❌ CUDA is not available")
            return False
    except ImportError:
        print("⚠️ PyTorch not installed - cannot check CUDA")
        return False
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
        return False

def test_ollama_gpu():
    """Test Ollama GPU usage"""
    print("\n🧪 TESTING OLLAMA GPU USAGE")
    print("=" * 35)
    
    import requests
    
    payload = {
        "model": "mistral-legal-q4:latest",
        "prompt": "What is a contract? Answer briefly.",
        "stream": False,
        "options": {
            "num_gpu": 1,
            "gpu_layers": -1,
            "low_vram": False,
            "num_ctx": 1024,
            "num_thread": 4,
            "num_batch": 4
        }
    }
    
    try:
        print("Sending test request...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:11434/api/generate",
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
            
            if response_time < 3:
                print("✅ Fast response suggests GPU acceleration")
            else:
                print("⚠️ Slow response might indicate CPU usage")
                
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FORCING GPU USAGE FOR OLLAMA")
    print("=" * 50)
    
    # Check GPU availability
    gpu_available = check_gpu_availability()
    
    if gpu_available:
        # Restart Ollama with GPU settings
        if restart_ollama_with_gpu():
            # Test GPU usage
            test_ollama_gpu()
        else:
            print("❌ Failed to restart Ollama with GPU settings")
    else:
        print("❌ GPU not available - cannot force GPU usage")
    
    print("\n" + "=" * 50)
    print("📊 CHECK TASK MANAGER GPU USAGE NOW!")
    print("Look for GPU memory usage in Task Manager > Performance > GPU")
    print("=" * 50)
