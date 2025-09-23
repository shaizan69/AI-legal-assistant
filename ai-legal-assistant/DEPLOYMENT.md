# AI Legal Assistant - Setup Guide

This guide covers the setup and deployment options for the AI Legal Assistant application.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ 
- Node.js 16+
- Git
- OpenAI API key (for AI features)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-legal-assistant
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables:**
```env
# Database (SQLite - no additional config needed)
DATABASE_URL=sqlite+aiosqlite:///./legal_assistant.db

# AI Services (Required)
OPENAI_API_KEY=your_openai_api_key_here

# JWT Authentication
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
```

### 3. Start the Application

```bash
# Using setup script (Recommended)
# Windows:
setup_environment.bat

# Linux/Mac:
./setup_environment.sh

# Manual setup:
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (in new terminal)
cd frontend
npm install
npm start
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: SQLite file (legal_assistant.db)

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS Elastic Beanstalk

1. **Prepare Application**
```bash
# Create deployment package
zip -r ai-legal-assistant.zip backend/ frontend/ -x "*/node_modules/*" "*/venv/*" "*/__pycache__/*"
```

2. **Deploy to Elastic Beanstalk**
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init ai-legal-assistant

# Create environment
eb create production

# Deploy
eb deploy
```

#### Using AWS Lambda + API Gateway

1. **Package Backend for Lambda**
```bash
cd backend
pip install -r requirements.txt -t .
zip -r lambda-deployment.zip .
```

2. **Deploy Frontend to S3 + CloudFront**
```bash
cd frontend
npm run build
aws s3 sync build/ s3://your-bucket-name
```

### Google Cloud Platform

#### Using App Engine

1. **Deploy Backend to App Engine**
```bash
# Create app.yaml in backend/
cd backend
gcloud app deploy
```

2. **Deploy Frontend to Firebase Hosting**
```bash
cd frontend
npm run build
firebase deploy
```

#### Using Cloud Functions

1. **Deploy Backend as Cloud Functions**
```bash
cd backend
gcloud functions deploy ai-legal-assistant --runtime python39 --trigger-http
```

### Microsoft Azure

#### Using Azure App Service

1. **Deploy Backend**
```bash
cd backend
az webapp up --name ai-legal-assistant-backend --runtime "PYTHON|3.9"
```

2. **Deploy Frontend**
```bash
cd frontend
npm run build
az webapp up --name ai-legal-assistant-frontend --runtime "NODE|16-lts"
```

## 🗄️ Database Setup

### SQLite (Default)

The application uses SQLite by default, which requires no additional setup:

```bash
# Database file is automatically created at:
# ./legal_assistant.db

# No additional configuration needed
# Database tables are created automatically on first run
```

### Database Migrations

```bash
# Run migrations (if using Alembic)
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"
```

### Optional: PostgreSQL for Production

If you want to use PostgreSQL for production:

1. **Install PostgreSQL locally**
2. **Update DATABASE_URL in .env**:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/legal_assistant
```

3. **Run migrations**:
```bash
cd backend
alembic upgrade head
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes | - |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `DEBUG` | Debug mode | No | False |
| `LOG_LEVEL` | Logging level | No | INFO |
| `CORS_ORIGINS` | Allowed CORS origins | No | ["http://localhost:3000"] |
| `UPLOAD_MAX_SIZE` | Max file upload size | No | 10485760 (10MB) |

### Security Configuration

1. **Change Default Secrets**
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Configure CORS**
```env
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

3. **Enable HTTPS**
```nginx
# nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of configuration
}
```

## 📊 Monitoring and Logging

### Application Logs

```bash
# View logs
# Backend logs
tail -f backend/logs/app.log

# Frontend logs (in terminal where npm start is running)
# Or check browser console for frontend logs
```

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Database health check
curl http://localhost:8000/api/health/db
```

### Monitoring with Prometheus

```bash
# Install Prometheus locally
# Download from: https://prometheus.io/download/

# Start Prometheus
./prometheus --config.file=prometheus.yml

# Install Grafana locally
# Download from: https://grafana.com/grafana/download

# Start Grafana
./grafana-server
```

## 🚀 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build and test application
        run: |
          cd backend
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          python -m pytest tests/
          
          cd ../frontend
          npm install
          npm run build
      
      - name: Deploy to production
        run: |
          # Your deployment commands here
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - cd backend
    - python -m venv venv
    - source venv/bin/activate
    - pip install -r requirements.txt
    - python -m pytest tests/
    - cd ../frontend
    - npm install
    - npm run build

deploy:
  stage: deploy
  script:
    - kubectl apply -f k8s/
  only:
    - main
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database credentials
   - Verify database is running
   - Check network connectivity

2. **File Upload Issues**
   - Check file size limits
   - Verify file permissions
   - Check disk space

3. **AI Features Not Working**
   - Verify OpenAI API key
   - Check API quota and billing
   - Review error logs

### Debug Mode

```bash
# Enable debug mode
export DEBUG=True
export LOG_LEVEL=DEBUG

# Start with debug logging
cd backend
python -m uvicorn app.main:app --reload --log-level debug
```

### Performance Optimization

1. **Database Optimization**
   - Add database indexes
   - Optimize queries
   - Use connection pooling

2. **Caching**
   - Enable Redis caching
   - Use CDN for static files
   - Implement response caching

3. **Scaling**
   - Use horizontal pod autoscaling
   - Implement load balancing
   - Use database read replicas

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository
4. Contact the development team
