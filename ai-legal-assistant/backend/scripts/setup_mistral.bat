@echo off
echo Setting up Mistral 7B for Legal Document Analysis...
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Run the setup script
echo Running Mistral setup...
python scripts\setup_mistral.py

if errorlevel 1 (
    echo Setup failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Start Ollama service: D:\Ollama\start_ollama.bat
echo 2. Start the backend: python -m uvicorn app.main:app --reload
echo 3. Use the legal document analysis features
echo.
echo All models are stored on D: drive (no C: drive usage)
echo Model size: ~4.1GB (much smaller than Llama 3-8B)
echo.
pause
