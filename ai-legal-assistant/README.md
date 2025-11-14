# AI-Powered Legal Document Assistant

A production-grade, end-to-end system for analyzing legal documents using AI. The system allows users to upload contracts/agreements (PDF/DOCX), extract text, analyze clauses, summarize content, detect risks, compare documents, and perform Q&A with documents using Large Language Models.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) - Full-featured backend with advanced processing
- **Edge Function**: Supabase Edge Functions (Deno/TypeScript) - Production-ready serverless API
- **Frontend**: React (JavaScript)
- **AI/NLP**: Google Gemini 2.5 Flash + InLegalBERT Embeddings
- **Database**: Supabase PostgreSQL + pgvector for semantic search
- **Storage**: Supabase Storage for document files
- **Deployment**: Supabase Edge Functions (production) + Local development setup

## 🚀 Features

### Core Features
- **Document Upload & Parsing**: Support for PDF files with multi-library extraction (pdfjs-dist, @pdf/pdftext, pdf2txt, unpdf)
- **AI Analysis**: Automatic summarization, risk detection, and clause analysis using Gemini 2.5 Flash
- **Q&A Interface**: Chat with documents using semantic search and contextual understanding
- **Document Comparison**: Compare two documents side-by-side with similarity scoring
- **Document Summarization**: Generate comprehensive summaries with structured data
- **Risk Analysis**: Comprehensive risk detection with categorization (Contractual, Compliance, Financial, Operational, Legal)
- **User Authentication**: JWT-based secure authentication
- **Financial Analysis**: Specialized extraction and analysis of monetary amounts, payment schedules, and financial terms
- **Legal Document Processing**: Optimized for Indian legal documents with InLegalBERT embeddings

### Advanced Features
- **Multi-pass Financial Analysis**: Comprehensive extraction of monetary amounts, payment schedules, tables, and calculations
- **Vector Similarity Search**: Semantic search using InLegalBERT embeddings with pgvector
- **Session Management**: Automatic cleanup of uploaded documents and chunks
- **Document Management**: Full CRUD operations for documents with cascade deletion
- **Feedback System**: User feedback collection for Q&A responses
- **Free User Mode**: Anonymous document analysis without authentication

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
- **API**: Hugging Face Inference API (public access, no API key required)
- **Note**: API key is optional - helps avoid rate limits but not required

### Key Features
- **Multi-pass Financial Analysis**: Comprehensive extraction of monetary amounts, payment schedules, and financial terms
- **Contextual Understanding**: Advanced prompt engineering for legal document analysis
- **Indian Legal Focus**: Specialized patterns for Indian currency formats (/-) and legal terminology
- **Table Data Processing**: Intelligent extraction and formatting of tabular information
- **Session Management**: Automatic cleanup of uploaded documents and chunks

## 📁 Project Structure

```
ai-legal-assistant/
├── backend/                 # FastAPI backend (full-featured)
│   ├── app/
│   │   ├── main.py         # FastAPI entrypoint
│   │   ├── api/            # API endpoints
│   │   │   ├── compare.py  # Document comparison
│   │   │   ├── summarize.py # Document summarization
│   │   │   ├── risks.py    # Risk analysis
│   │   │   ├── qa.py       # Q&A endpoints
│   │   │   ├── free.py     # Free user endpoints
│   │   │   └── upload.py   # Document upload
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Pydantic schemas & ORM models
│   │   ├── services/       # Business logic
│   │   └── tests/          # Test cases
│   ├── venv/               # Python virtual environment
│   └── requirements.txt
├── supabase/
│   └── functions/
│       └── api/
│           ├── index.ts    # Edge Function (production API)
│           ├── vector_search_setup.sql  # Vector search setup
│           └── verify_vector_setup.sql  # Verification queries
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

- Python 3.9+ (for backend development)
- Node.js 16+ (for frontend and Edge Function deployment)
- Git
- Google Gemini API Key (free tier available)
- Supabase Account (for production deployment)
- Supabase CLI (for Edge Function deployment)

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

### Edge Function API (Production)

The Edge Function provides a complete REST API with all features:

#### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

#### Document Management
- `GET /documents` - List user documents (with pagination)
- `GET /documents/:id` - Get specific document
- `DELETE /documents/:id` - Delete document (with cascade cleanup)
- `POST /upload/supabase` - Upload document metadata
- `POST /free/upload` - Free user document upload

#### Document Analysis
- `POST /summarize` - Generate document summary
- `GET /summarize/:id` - Get existing summary
- `GET /summarize` - List all summaries
- `DELETE /summarize/:id` - Delete summary

#### Risk Analysis
- `POST /free/analyze-risks` - Analyze risks (free user)
- `GET /risks/:id` - Get risk analysis for document
- `GET /risks` - List all risk analyses
- `DELETE /risks/:id` - Delete risk analysis

#### Document Comparison
- `POST /compare` - Compare two documents
- `GET /compare/:id` - Get specific comparison
- `GET /compare` - List all comparisons
- `DELETE /compare/:id` - Delete comparison

#### Q&A System
- `POST /qa/ask` - Ask question (authenticated)
- `POST /free/ask` - Ask question (free user)
- `GET /qa/sessions` - List Q&A sessions
- `GET /qa/sessions/:id` - Get specific session
- `GET /qa/sessions/:id/questions` - Get session questions
- `PUT /qa/questions/:id/feedback` - Provide feedback
- `DELETE /qa/sessions/:id` - Delete session

#### Free User Endpoints
- `POST /free/upload` - Upload document
- `POST /free/session` - Create session
- `GET /free/session` - Get latest session
- `POST /free/ask` - Ask question
- `POST /free/analyze-risks` - Analyze risks
- `DELETE /free/session/:id` - End session
- `POST /free/cleanup-orphaned` - Cleanup orphaned documents

### Backend API (Development)

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

## 🚀 Edge Function Deployment

### Setup Supabase Edge Functions

1. **Install Supabase CLI**:
```bash
npm install -g supabase
```

2. **Login to Supabase**:
```bash
supabase login
```

3. **Link your project**:
```bash
supabase link --project-ref your-project-ref
```

4. **Set Environment Variables** in Supabase Dashboard:
   - `GEMINI_API_KEY` - Your Google Gemini API key
   - `GEMINI_MODEL` - Model name (default: `gemini-2.5-flash`)
   - `HUGGINGFACE_API_KEY` - Optional, helps avoid rate limits
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key

5. **Deploy Edge Function**:
```bash
npx supabase functions deploy api --project-ref your-project-ref --no-verify-jwt
```

6. **Setup Vector Search** (run in Supabase SQL Editor):
```sql
-- Run the SQL from: supabase/functions/api/vector_search_setup.sql
```

### Edge Function Features

✅ **Complete Feature Parity** with Backend:
- All document management endpoints
- Full CRUD for comparisons, summaries, risks
- Complete Q&A system with feedback
- Free user mode with automatic cleanup
- Multi-library PDF extraction (pdfjs-dist, @pdf/pdftext, pdf2txt, unpdf)
- InLegalBERT embeddings (no API key required)
- Vector similarity search with pgvector
- Financial analysis with multi-pass extraction

## 🎯 Current Status

### ✅ Implemented Features

#### Backend (FastAPI)
- **Gemini 2.5 Flash Integration**: Fully configured and operational
- **InLegalBERT Embeddings**: Optimized for Indian legal documents
- **Financial Analysis**: Multi-pass extraction of monetary amounts and payment schedules
- **Document Processing**: PDF/DOCX upload and text extraction with pdfplumber, PyMuPDF, pymupdf4llm
- **Q&A System**: Contextual question answering with document analysis
- **Session Management**: Automatic cleanup of uploaded documents
- **Table Data Processing**: Intelligent extraction and formatting
- **Indian Legal Focus**: Specialized patterns for Indian currency and legal terms

#### Edge Function (Supabase)
- **Complete API**: All backend features implemented in Deno/TypeScript
- **PDF Extraction**: Multi-library fallback (pdfjs-dist → @pdf/pdftext → pdf2txt → unpdf)
- **InLegalBERT**: Hugging Face API integration (no API key required)
- **Vector Search**: pgvector integration for semantic search
- **Document Comparison**: Full CRUD operations
- **Document Summarization**: Full CRUD operations
- **Risk Analysis**: Full CRUD operations
- **Q&A System**: Complete with feedback collection
- **Document Management**: Full CRUD with cascade deletion
- **Free User Mode**: Anonymous document analysis

### 🔄 Recent Updates
- ✅ **Complete Edge Function Implementation**: All backend features now available in Edge Function
- ✅ **PDF Extraction Fixed**: Multi-library approach with proper error handling
- ✅ **InLegalBERT Integration**: Works without API key (optional for rate limits)
- ✅ **Document Comparison API**: Full CRUD operations
- ✅ **Document Summarization API**: Full CRUD operations
- ✅ **Risk Analysis CRUD**: Complete GET/DELETE operations
- ✅ **QA Session CRUD**: Complete GET/PUT operations for sessions and feedback
- ✅ **Document Management**: Full CRUD with proper cascade deletion
- ✅ **Vector Search**: pgvector integration for semantic similarity
- ✅ **Financial Analysis**: Multi-pass extraction integrated
- ✅ **User Authentication**: JWT-based auth for all endpoints

## 🔧 Troubleshooting

### PDF Extraction Issues

If PDF extraction fails, the Edge Function uses a multi-library fallback approach:

1. **pdfjs-dist** (PDF.js) - Primary method, works in Deno environment
2. **@pdf/pdftext** - Fast extraction for simple PDFs
3. **pdf2txt** - Complex layout handling
4. **unpdf** - Final fallback

**Common Issues:**
- **"Module not found"**: Libraries are auto-imported, ensure network connectivity
- **"Insufficient text"**: PDF may be image-based or encrypted - try OCR conversion
- **"extractText is not a function"**: Fixed with proper module detection

### InLegalBERT Embeddings

- **No API Key Required**: Works without Hugging Face API key (public access)
- **Rate Limits**: May hit rate limits without API key - set `HUGGINGFACE_API_KEY` to avoid
- **Model Loading**: First request may take longer if model is loading (503 error)

### Vector Search Setup

Ensure you've run the vector search setup SQL:
```sql
-- From: supabase/functions/api/vector_search_setup.sql
CREATE EXTENSION IF NOT EXISTS vector;
-- ... (rest of setup)
```

### Deployment Issues

- **"INACTIVE" project**: Activate your Supabase project in dashboard
- **Function timeout**: Large PDFs may take time - consider async processing
- **CORS errors**: CORS headers are configured, check browser console

## 📞 Support

For support, please open an issue in the GitHub repository.
