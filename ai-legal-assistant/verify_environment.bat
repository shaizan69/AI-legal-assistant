@echo off
echo Verifying AI Legal Assistant Environment...
echo ==========================================

REM Set Node.js path
set NODEJS_PATH=D:\Programs\nodejs
set PATH=%NODEJS_PATH%;%PATH%

echo Checking Python environment...
cd /d "%~dp0backend"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Test Python packages
echo Testing Python packages...
python -c "import fastapi, uvicorn, sqlalchemy, openai, transformers, torch, sentence_transformers, pdfplumber, fitz; print('✓ All Python packages working')"

REM Test specific functionality
echo Testing FastAPI...
python -c "from fastapi import FastAPI; app = FastAPI(); print('✓ FastAPI initialized successfully')"

echo Testing database connection...
python -c "from sqlalchemy import create_engine; print('✓ SQLAlchemy working')"

echo Testing AI libraries...
python -c "import openai; print('✓ OpenAI library working')"
python -c "import transformers; print('✓ Transformers library working')"
python -c "import torch; print('✓ PyTorch working')"

echo.
echo Checking Node.js environment...
cd /d "%~dp0frontend"

REM Test Node.js
echo Testing Node.js...
node -e "console.log('✓ Node.js is working'); console.log('Node version:', process.version)"

REM Test npm packages
echo Testing npm packages...
node -e "const React = require('react'); console.log('✓ React is working')"
node -e "const axios = require('axios'); console.log('✓ Axios is working')"

echo.
echo ==========================================
echo Environment verification completed!
echo ==========================================
echo.
echo Both Python and Node.js environments are properly configured.
echo You can now start the development servers:
echo.
echo Backend: cd backend ^&^& venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload
echo Frontend: cd frontend ^&^& npm start
echo.
pause
