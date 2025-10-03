#!/usr/bin/env python3
"""
Setup script for Mistral Legal Q4 with Ollama configured to use D: drive
"""

import subprocess
import sys
import time
import requests
import os
import json

def run_command(cmd, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return result.returncode == 0
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {e}")
        return False

def check_ollama_installed():
    """Check if Ollama is installed"""
    print("Checking if Ollama is installed...")
    return run_command("ollama --version", check=False)

def install_ollama():
    """Install Ollama"""
    print("Installing Ollama...")
    print("Please download and install Ollama from: https://ollama.ai/download/windows")
    print("After installation, add Ollama to your PATH and restart this script.")
    return False

def configure_ollama_d_drive():
    """Configure Ollama to use D: drive"""
    print("Configuring Ollama to use D: drive...")
    
    # Create D:\Ollama directory
    ollama_dir = "D:\\Ollama"
    if not os.path.exists(ollama_dir):
        os.makedirs(ollama_dir)
        print(f"Created directory: {ollama_dir}")
    
    # Set environment variable
    os.environ['OLLAMA_MODELS'] = ollama_dir
    print(f"Set OLLAMA_MODELS environment variable to: {ollama_dir}")
    
    # Create a batch file to start Ollama with D: drive
    batch_content = f"""@echo off
echo Starting Ollama with models stored on D: drive...
set OLLAMA_MODELS={ollama_dir}
ollama serve
"""
    
    batch_file = os.path.join(ollama_dir, "start_ollama.bat")
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"Created startup script: {batch_file}")
    return True

def start_ollama():
    """Start Ollama service"""
    print("Starting Ollama service...")
    try:
        # Set environment variable
        os.environ['OLLAMA_MODELS'] = "D:\\Ollama"
        
        # Try to start Ollama in the background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)  # Wait for service to start
        
        # Test if it's running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama service started successfully")
            return True
        else:
            print("✗ Ollama service failed to start")
            return False
    except Exception as e:
        print(f"✗ Failed to start Ollama: {e}")
        return False

def check_ollama_running():
    """Check if Ollama is running"""
    print("Checking if Ollama is running...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running")
            return True
        else:
            print("✗ Ollama is not responding")
            return False
    except Exception as e:
        print("✗ Ollama is not running")
        return False

def pull_mistral_model():
    """Pull Mistral Legal Q4 model"""
    print("Pulling Mistral Legal Q4 model (this may take a while)...")
    print("Model size: ~4.4GB, ensure sufficient disk and VRAM")
    return run_command("ollama pull mistral-legal-q4:latest")

def check_mistral_model():
    """Check if Mistral Legal Q4 model is available"""
    print("Checking if Mistral Legal Q4 model is available...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            if 'mistral-legal-q4:latest' in model_names:
                print("✓ Mistral Legal Q4 model is available")
                return True
            else:
                print("✗ Mistral Legal Q4 model not found")
                print(f"Available models: {model_names}")
                return False
        else:
            print("✗ Failed to check models")
            return False
    except Exception as e:
        print(f"✗ Error checking models: {e}")
        return False

def create_legal_mistral_model():
    """Optional: prepare a Modelfile overlay (not required)."""
    print("Preparing optional legal overlay Modelfile (base: Mistral Legal Q4)...")
    try:
        modelfile_path = "D:\\Ollama\\Modelfile.legal"
        modelfile_content = (
            "FROM mistral-legal-q4:latest\n\n"
            "SYSTEM \"\"\"You are a specialized legal document analysis assistant.\"\"\"\n"
        )
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        print(f"Created Modelfile: {modelfile_path}")
    except Exception:
        pass
    return True

def test_mistral():
    """Test Mistral Legal Q4 model"""
    print("Testing Mistral Legal Q4 model...")
    try:
        payload = {
            "model": "mistral-legal-q4:latest",
            "prompt": "What is a contract? Provide a brief legal definition.",
            "stream": False
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print("✓ Mistral Legal Q4 test successful")
            print(f"Response: {result.get('response', 'No response')[:200]}...")
            return True
        else:
            print(f"✗ Mistral Legal Q4 test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Mistral Legal Q4 test failed: {e}")
        return False

def test_legal_model():
    """Test the legal flow using Mistral Legal Q4 base"""
    print("Testing legal document analysis model...")
    try:
        payload = {
            "model": "mistral-legal-q4:latest",
            "prompt": "Analyze this clause: 'The Company shall not be liable for any indirect, incidental, special, or consequential damages.' What are the potential risks?",
            "stream": False
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print("✓ Legal test successful")
            print(f"Response: {result.get('response', 'No response')[:300]}...")
            return True
        else:
            print(f"✗ Legal test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Legal test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Mistral Legal Q4 Setup for Legal Document Analysis")
    print("=" * 50)
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("\nOllama is not installed.")
        install_ollama()
        return False
    # Configure Ollama to use D: drive
    print("\nConfiguring Ollama to use D: drive...")
    configure_ollama_d_drive()
    # Check if Ollama is running
    if not check_ollama_running():
        print("\nOllama is not running. Starting it...")
        if not start_ollama():
            print("Failed to start Ollama. Please start it manually: ollama serve")
            return False
    # Check if Mistral Legal Q4 model is available
    if not check_mistral_model():
        print("\nMistral Legal Q4 model not found. Pulling it...")
        if not pull_mistral_model():
            print("Failed to pull Mistral Legal Q4 model")
            return False
    # Optional overlay
    print("\nPreparing legal document analysis overlay (optional)...")
    if not create_legal_mistral_model():
        print("Failed to prepare legal overlay")
        return False
    # Test Mistral Legal Q4 (single-model policy)
    if not test_legal_model():
        print("Failed to test Mistral Legal Q4 legal flow")
        return False
    if not test_mistral():
        print("Failed to test Mistral Legal Q4 base generate")
        return False
    print("\n" + "=" * 50)
    print("✓ Setup completed successfully!")
    print("=" * 50)
    print("\nYour Mistral Legal Q4 setup is ready!")
    print("Model: mistral-legal-q4:latest (stored on D: drive)")
    print("\nYou can now:")
    print("1. Start your backend: python -m uvicorn app.main:app --reload")
    print("2. Use the legal document analysis features")
    print("3. All models are stored on D: drive (no C: drive usage)")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
