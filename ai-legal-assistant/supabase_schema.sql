-- Supabase Database Schema for AI Legal Assistant
-- This script creates the complete database schema with pgvector support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

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
    file_url VARCHAR(1000),  -- Supabase public URL
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    supabase_path VARCHAR(500),  -- Supabase storage path
    
    -- Document content
    extracted_text TEXT,
    text_hash VARCHAR(64),
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    
    -- Document metadata
    document_type VARCHAR(100),  -- contract, agreement, etc.
    title VARCHAR(500),
    parties JSONB,  -- List of parties involved
    effective_date TIMESTAMP WITH TIME ZONE,
    expiration_date TIMESTAMP WITH TIME ZONE,
    
    -- Processing status
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    processing_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Foreign keys
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);

-- Create document_chunks table with pgvector support
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    
    -- Vector information using pgvector
    embedding_id VARCHAR(100) UNIQUE,
    embedding VECTOR(1536),  -- OpenAI ada-002 dimension, adjust as needed
    has_embedding BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- Additional metadata for the chunk
    
    -- Chunk metadata
    start_position INTEGER,  -- Position in original document
    end_position INTEGER,
    section_title VARCHAR(500),
    clause_number VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document_analyses table
CREATE TABLE IF NOT EXISTS document_analyses (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,  -- summary, risk, comparison, etc.
    
    -- Analysis results
    summary TEXT,
    structured_data JSONB,
    confidence_score FLOAT,
    
    -- Analysis metadata
    model_used VARCHAR(100),
    processing_time FLOAT,  -- seconds
    token_count INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create risk_analyses table
CREATE TABLE IF NOT EXISTS risk_analyses (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    risk_level VARCHAR(20) NOT NULL,  -- High, Medium, Low
    risk_type VARCHAR(100) NOT NULL,  -- auto_renewal, liability, etc.
    description TEXT NOT NULL,
    location VARCHAR(500),  -- Where in document
    recommendation TEXT,
    
    -- Risk scoring
    severity_score FLOAT,  -- 0.0 to 1.0
    likelihood_score FLOAT,  -- 0.0 to 1.0
    overall_score FLOAT,  -- Combined score
    
    -- Additional metadata
    clause_reference VARCHAR(200),
    page_number INTEGER,
    line_number INTEGER,
    
    -- Timestamps
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
    
    -- Answer quality metrics
    confidence_score FLOAT,  -- 0.0 to 1.0
    context_used TEXT,  -- Context from document
    sources JSONB,  -- References to document sections
    
    -- Processing metadata
    processing_time FLOAT,  -- seconds
    model_used VARCHAR(100),
    token_count INTEGER,
    
    -- User feedback
    is_helpful BOOLEAN,
    user_rating INTEGER,  -- 1-5 scale
    feedback TEXT,
    
    -- Timestamps
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
    
    -- Comparison results
    summary TEXT,
    key_differences JSONB,  -- List of differences
    similarities JSONB,  -- List of similarities
    recommendations JSONB,  -- List of recommendations
    
    -- Comparison metadata
    comparison_type VARCHAR(50) NOT NULL,  -- template, version, custom
    similarity_score FLOAT,  -- Overall similarity 0.0 to 1.0
    risk_comparison JSONB,  -- Risk analysis comparison
    
    -- Processing metadata
    processing_time FLOAT,  -- seconds
    model_used VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_documents_owner_id ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_text_hash ON documents(text_hash);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_id ON document_chunks(embedding_id);
CREATE INDEX IF NOT EXISTS idx_document_analyses_document_id ON document_analyses(document_id);
CREATE INDEX IF NOT EXISTS idx_document_analyses_type ON document_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_risk_analyses_document_id ON risk_analyses(document_id);
CREATE INDEX IF NOT EXISTS idx_risk_analyses_level ON risk_analyses(risk_level);
CREATE INDEX IF NOT EXISTS idx_qa_sessions_user_id ON qa_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_qa_sessions_document_id ON qa_sessions(document_id);
CREATE INDEX IF NOT EXISTS idx_qa_questions_session_id ON qa_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_comparisons_user_id ON comparisons(user_id);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_documents_text_search ON documents USING gin(to_tsvector('english', extracted_text));
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_search ON document_chunks USING gin(to_tsvector('english', content));

-- Create vector similarity search index using pgvector
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_cosine ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create HNSW index for better vector search performance (if supported)
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw ON document_chunks 
-- USING hnsw (embedding vector_cosine_ops);

-- Enable Row Level Security (RLS) for data protection
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE comparisons ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (basic - adjust based on your auth requirements)
-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users FOR ALL USING (auth.uid()::text = id::text);
CREATE POLICY "Users can view own documents" ON documents FOR ALL USING (auth.uid()::text = owner_id::text);
CREATE POLICY "Users can view own document chunks" ON document_chunks FOR ALL USING (
    document_id IN (SELECT id FROM documents WHERE auth.uid()::text = owner_id::text)
);
CREATE POLICY "Users can view own analyses" ON document_analyses FOR ALL USING (
    document_id IN (SELECT id FROM documents WHERE auth.uid()::text = owner_id::text)
);
CREATE POLICY "Users can view own risk analyses" ON risk_analyses FOR ALL USING (
    document_id IN (SELECT id FROM documents WHERE auth.uid()::text = owner_id::text)
);
CREATE POLICY "Users can view own qa sessions" ON qa_sessions FOR ALL USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can view own qa questions" ON qa_questions FOR ALL USING (
    session_id IN (SELECT id FROM qa_sessions WHERE auth.uid()::text = user_id::text)
);
CREATE POLICY "Users can view own comparisons" ON comparisons FOR ALL USING (auth.uid()::text = user_id::text);

-- Insert sample data (optional - for development/testing)
-- This can be uncommented for development/testing
/*
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_verified) 
VALUES ('admin@legalassistant.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.8K2O', 'Admin User', TRUE, TRUE);
*/
