# AI-Powered Legal Document Assistant

A production-grade, end-to-end system for analyzing legal documents using AI. The system allows users to upload contracts/agreements (PDF/DOCX), extract text, analyze clauses, summarize content, detect risks, and perform Q&A with documents using Large Language Models.

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React (JavaScript)
- **AI/NLP**: Google Gemini 2.5 Flash + InLegalBERT Embeddings
- **Database**: Supabase PostgreSQL + pgvector
- **Deployment**: Local development setup

## 🚀 Features

- **Document Upload & Parsing**: Support for PDF/DOCX files with OCR capabilities
- **AI Analysis**: Automatic summarization, risk detection, and clause analysis using Gemini 2.5 Flash
- **Q&A Interface**: Chat with documents using semantic search and contextual understanding
- **Contract Comparison**: Compare contracts against templates or previous versions
- **User Authentication**: JWT-based secure authentication
- **Real-time Notifications**: Calendar integration and email reminders
- **Financial Analysis**: Specialized extraction and analysis of monetary amounts, payment schedules, and financial terms
- **Legal Document Processing**: Optimized for Indian legal documents with InLegalBERT embeddings

## 🤖 AI Models & Capabilities

### Primary LLM: Google Gemini 2.5 Flash
- **Model**: `gemini-2.5-flash`
- **Capabilities**: 
  - Document summarization and analysis
  - Risk detection and assessment
  - Contract comparison and analysis
  - Q&A with contextual understanding
  - Financial data extraction and analysis
  - Legal document interpretation
- **API**: Google Generative AI API
- **Cost**: Free tier available

### Embeddings: InLegalBERT
- **Model**: `law-ai/InLegalBERT`
- **Purpose**: Semantic search and document chunking
- **Specialization**: Optimized for Indian legal documents
- **Dimensions**: 768
- **Usage**: Document similarity search and context retrieval

### Key Features
- **Multi-pass Financial Analysis**: Comprehensive extraction of monetary amounts, payment schedules, and financial terms
- **Contextual Understanding**: Advanced prompt engineering for legal document analysis
- **Indian Legal Focus**: Specialized patterns for Indian currency formats (/-) and legal terminology
- **Table Data Processing**: Intelligent extraction and formatting of tabular information
- **Session Management**: Automatic cleanup of uploaded documents and chunks

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
- Google Gemini API Key (free tier available)

### Getting Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Add it to your `.env` file as `GEMINI_API_KEY=your_api_key_here`

### Environment Setup

1. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

2. Update the `.env` file with your credentials:
```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./legal_assistant.db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=legal_assistant
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# AI Services - Gemini API (Primary LLM)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Embeddings
EMBEDDING_MODEL=law-ai/InLegalBERT

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

## 🎯 Current Status

### ✅ Implemented Features
- **Gemini 2.5 Flash Integration**: Fully configured and operational
- **InLegalBERT Embeddings**: Optimized for Indian legal documents
- **Financial Analysis**: Multi-pass extraction of monetary amounts and payment schedules
- **Document Processing**: PDF/DOCX upload and text extraction
- **Q&A System**: Contextual question answering with document analysis
- **Session Management**: Automatic cleanup of uploaded documents
- **Table Data Processing**: Intelligent extraction and formatting
- **Indian Legal Focus**: Specialized patterns for Indian currency and legal terms

### 🔄 Recent Updates
- Migrated from Groq to Google Gemini 2.5 Flash
- Removed table formatting in favor of clean text output
- Eliminated chunk references from responses
- Enhanced financial data extraction capabilities
- Improved contextual understanding for legal documents

## 📞 Support

For support, please open an issue in the GitHub repository.
