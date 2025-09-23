# AI-Powered Legal Document Assistant

A production-grade, end-to-end system for analyzing legal documents using AI. The system allows users to upload contracts/agreements (PDF/DOCX), extract text, analyze clauses, summarize content, detect risks, and perform Q&A with documents using Large Language Models.

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React (JavaScript)
- **AI/NLP**: OpenAI/HuggingFace LLMs + Embeddings
- **Database**: SQLite + FAISS Vector DB
- **Deployment**: Local development setup

## 🚀 Features

- **Document Upload & Parsing**: Support for PDF/DOCX files with OCR capabilities
- **AI Analysis**: Automatic summarization, risk detection, and clause analysis
- **Q&A Interface**: Chat with documents using semantic search
- **Contract Comparison**: Compare contracts against templates or previous versions
- **User Authentication**: JWT-based secure authentication
- **Real-time Notifications**: Calendar integration and email reminders

## 📁 Project Structure

```
ai-legal-assistant/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI entrypoint
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Pydantic schemas & ORM models
│   │   ├── services/       # Business logic
│   │   └── tests/          # Test cases
│   ├── venv/               # Python virtual environment
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── App.js
│   ├── node_modules/       # Node.js dependencies
│   └── package.json
├── db/                     # Database files
│   └── init.sql           # DB schema
└── .env.example           # Environment variables template
```

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.9+ 
- Node.js 16+
- Git

### Environment Setup

1. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

2. Update the `.env` file with your credentials:
```env
# Database (SQLite - no configuration needed)
DATABASE_URL=sqlite+aiosqlite:///./legal_assistant.db

# AI Services
OPENAI_API_KEY=your_openai_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Optional)
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=noreply@yourdomain.com
```

### Quick Setup

Run the setup script to automatically configure the environment:

```bash
# Windows
setup_environment.bat

# Linux/Mac
./setup_environment.sh
```

### Manual Setup

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## 📚 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🔒 Security

- JWT-based authentication
- File upload validation
- Input sanitization
- CORS configuration
- Rate limiting

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support, please open an issue in the GitHub repository.
