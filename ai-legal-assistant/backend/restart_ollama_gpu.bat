@echo off
echo Stopping Ollama...
taskkill /f /im ollama.exe 2>nul
timeout /t 3 /nobreak >nul

echo Setting GPU environment variables...
set CUDA_VISIBLE_DEVICES=0
set OLLAMA_GPU_LAYERS=-1
set OLLAMA_NUM_GPU=1
set OLLAMA_MODELS=D:\Ollama

echo Starting Ollama with GPU settings...
start "Ollama GPU" ollama serve

echo Waiting for Ollama to start...
timeout /t 5 /nobreak >nul

echo Testing GPU usage...
python -c "import requests; r=requests.post('http://localhost:11434/api/generate', json={'model': 'mistral-legal-q4:latest', 'prompt': 'Test GPU', 'stream': False, 'options': {'num_gpu': 1, 'gpu_layers': -1, 'low_vram': False}}); print('GPU Test:', r.status_code)"

echo Done! Check Task Manager GPU usage now.
pause
