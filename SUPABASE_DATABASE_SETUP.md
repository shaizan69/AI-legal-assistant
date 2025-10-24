# Supabase Database Setup

## Quick Fix - Create Tables in Supabase

You're absolutely right! The bucket is already set up. We just need to create the database tables in your Supabase Postgres database.

### Step 1: Check if Tables Exist

Go to your Supabase Dashboard:
1. **URL**: https://supabase.com/dashboard/project/iuxqomqbxfoetnieaorw
2. **Navigate to**: **SQL Editor**
3. **Run this query** to check if tables exist:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'documents', 'qa_sessions', 'qa_questions', 'document_chunks');
```

### Step 2: Create Tables (if they don't exist)

If the query above returns empty results, run this SQL to create all tables:

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    company VARCHAR(255),
    role VARCHAR(100),
    phone VARCHAR(20),
    bio TEXT
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(1000),
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    extracted_text TEXT,
    text_hash VARCHAR(64),
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    document_type VARCHAR(100),
    title VARCHAR(500),
    parties JSONB,
    effective_date TIMESTAMP WITH TIME ZONE,
    expiration_date TIMESTAMP WITH TIME ZONE,
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    supabase_path VARCHAR(500)
);

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    embedding_id VARCHAR(100),
    has_embedding BOOLEAN DEFAULT FALSE,
    start_position INTEGER,
    end_position INTEGER,
    section_title VARCHAR(500),
    clause_number VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create qa_sessions table
CREATE TABLE IF NOT EXISTS qa_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    session_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    total_questions INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create qa_questions table
CREATE TABLE IF NOT EXISTS qa_questions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES qa_sessions(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT,
    confidence_score FLOAT,
    context_used TEXT,
    sources JSONB,
    processing_time FLOAT,
    model_used VARCHAR(100),
    token_count INTEGER,
    is_helpful BOOLEAN,
    user_rating INTEGER,
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    answered_at TIMESTAMP WITH TIME ZONE
);

-- Create comparisons table
CREATE TABLE IF NOT EXISTS comparisons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document1_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    document2_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    comparison_name VARCHAR(255),
    summary TEXT,
    key_differences JSONB,
    similarities JSONB,
    recommendations JSONB,
    comparison_type VARCHAR(50) NOT NULL,
    similarity_score FLOAT,
    risk_comparison JSONB,
    processing_time FLOAT,
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_documents_owner_id ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_text_hash ON documents(text_hash);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_qa_sessions_user_id ON qa_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_qa_sessions_document_id ON qa_sessions(document_id);
CREATE INDEX IF NOT EXISTS idx_qa_questions_session_id ON qa_questions(session_id);
```

### Step 3: Deploy the Edge Function

1. **Go to**: https://supabase.com/dashboard/project/iuxqomqbxfoetnieaorw/functions
2. **Edit the `api` function**
3. **Copy the complete code from**: `ai-legal-assistant/supabase/functions/api/index.ts`
4. **Paste and deploy**

### Step 4: Test

1. **Hard refresh your Vercel app** (Ctrl+F5)
2. **Login** with `test@example.com` / `testpass`
3. **Upload a document** - should now work!
4. **Check Documents section** - should see uploaded files!

## Why This Works

- ✅ **Storage**: Uses your existing `legal-documents` bucket
- ✅ **Database**: Creates tables in your Supabase Postgres database
- ✅ **Edge Function**: Connects to both storage and database
- ✅ **Same Logic**: Matches the original working backend exactly

The Edge Function will now:
1. Upload files to your existing bucket
2. Store document metadata in the database
3. Create QA sessions in the database
4. Fetch documents from the database

**No new buckets needed - just database tables!**
