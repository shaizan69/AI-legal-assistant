@echo off
REM AI Legal Assistant Setup Script for Windows
REM This script sets up the development environment for the AI Legal Assistant

echo 🚀 Setting up AI Legal Assistant...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)
echo [SUCCESS] Docker and Docker Compose are installed

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.9+ first.
    exit /b 1
)
echo [SUCCESS] Python is installed

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 16+ first.
    exit /b 1
)
echo [SUCCESS] Node.js is installed

REM Create environment file
if not exist .env (
    echo [INFO] Creating .env file from template...
    copy .env.example .env
    echo [WARNING] Please update .env file with your API keys and configuration
    echo [SUCCESS] .env file created
) else (
    echo [INFO] .env file already exists
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist backend\uploads mkdir backend\uploads
if not exist backend\data mkdir backend\data
if not exist backend\logs mkdir backend\logs
if not exist frontend\build mkdir frontend\build
echo [SUCCESS] Directories created

REM Setup backend
echo [INFO] Setting up backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
cd ..
echo [SUCCESS] Backend setup completed

REM Setup frontend
echo [INFO] Setting up frontend...
cd frontend
echo [INFO] Installing Node.js dependencies...
npm install
cd ..
echo [SUCCESS] Frontend setup completed

REM Build Docker images
echo [INFO] Building Docker images...
docker-compose build
echo [SUCCESS] Docker images built

echo.
echo [SUCCESS] 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Update .env file with your API keys
echo 2. Run 'docker-compose up -d' to start the application
echo 3. Visit http://localhost:3000 to access the frontend
echo 4. Visit http://localhost:8000/docs to access the API documentation
echo.
echo For development:
echo - Backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo - Frontend: cd frontend ^&^& npm start
echo.

pause
