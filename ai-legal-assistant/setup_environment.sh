#!/bin/bash

echo "Setting up AI Legal Assistant Environment..."
echo "=========================================="

# Set Node.js path
export NODEJS_PATH="/d/Programs/nodejs"
export PATH="$NODEJS_PATH:$PATH"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found at $NODEJS_PATH"
    echo "Please verify the Node.js installation path"
    exit 1
fi

echo "Node.js version:"
node --version

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify Python installation
echo "Verifying Python packages..."
python -c "import fastapi, uvicorn, sqlalchemy, openai, transformers; print('Python packages installed successfully')"

# Navigate to frontend directory
cd "../frontend"

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Verify Node.js installation
echo "Verifying Node.js packages..."
node -e "console.log('Node.js packages installed successfully')"

echo ""
echo "=========================================="
echo "Environment setup completed successfully!"
echo "=========================================="
echo ""
echo "To start the backend server:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --reload"
echo ""
echo "To start the frontend server:"
echo "  cd frontend"
echo "  npm start"
echo ""
