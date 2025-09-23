#!/bin/bash

# AI Legal Assistant Setup Script
# This script sets up the development environment for the AI Legal Assistant

set -e

echo "🚀 Setting up AI Legal Assistant..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9+ first."
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $python_version is installed"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+ first."
        exit 1
    fi
    
    node_version=$(node --version)
    print_success "Node.js $node_version is installed"
}

# Create environment file
create_env_file() {
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please update .env file with your API keys and configuration"
        print_success ".env file created"
    else
        print_status ".env file already exists"
    fi
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Backend setup completed"
    cd ..
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    print_success "Frontend setup completed"
    cd ..
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p backend/uploads
    mkdir -p backend/data
    mkdir -p backend/logs
    mkdir -p frontend/build
    
    print_success "Directories created"
}

# Build Docker images
build_docker() {
    print_status "Building Docker images..."
    
    docker-compose build
    
    print_success "Docker images built"
}

# Main setup function
main() {
    echo "🔧 AI Legal Assistant Setup"
    echo "=========================="
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_docker
    check_python
    check_node
    
    # Create environment file
    create_env_file
    
    # Create directories
    create_directories
    
    # Setup backend
    setup_backend
    
    # Setup frontend
    setup_frontend
    
    # Build Docker images
    build_docker
    
    echo ""
    print_success "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update .env file with your API keys"
    echo "2. Run 'docker-compose up -d' to start the application"
    echo "3. Visit http://localhost:3000 to access the frontend"
    echo "4. Visit http://localhost:8000/docs to access the API documentation"
    echo ""
    echo "For development:"
    echo "- Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "- Frontend: cd frontend && npm start"
    echo ""
}

# Run main function
main "$@"
