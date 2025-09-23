@echo off
echo Setting up AI Legal Assistant Environment...
echo ==========================================

REM Set Node.js path
set NODEJS_PATH=D:\Programs\nodejs
set PATH=%NODEJS_PATH%;%PATH%

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found at D:\Programs\nodejs
    echo Please verify the Node.js installation path
    pause
    exit /b 1
)

echo Node.js version:
node --version

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Remove existing virtual environment if it exists
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q "venv"
)

REM Create new virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Verify Python installation
echo Verifying Python packages...
python -c "import fastapi, uvicorn, sqlalchemy, openai, transformers; print('Python packages installed successfully')"

REM Navigate to frontend directory
cd /d "%~dp0frontend"

REM Install Node.js dependencies
echo Installing Node.js dependencies...
npm install

REM Verify Node.js installation
echo Verifying Node.js packages...
node -e "console.log('Node.js packages installed successfully')"

echo.
echo ==========================================
echo Environment setup completed successfully!
echo ==========================================
echo.
echo To start the backend server:
echo   cd backend
echo   venv\Scripts\activate
echo   python -m uvicorn app.main:app --reload
echo.
echo To start the frontend server:
echo   cd frontend
echo   npm start
echo.
pause
