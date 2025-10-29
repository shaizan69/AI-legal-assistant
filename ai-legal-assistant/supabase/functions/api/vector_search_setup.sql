-- SQL Setup for Vector Search in Edge Functions
-- Run this in your Supabase SQL Editor to enable pgvector similarity search

-- 1. Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create function for vector similarity search
CREATE OR REPLACE FUNCTION search_similar_chunks(
  query_vector text,  -- Vector as text: "[0.1,0.2,...]"
  document_id int,
  limit_count int DEFAULT 10
)
RETURNS TABLE (
  chunk_index int,
  similarity_score float,
  content text
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    dc.chunk_index,
    1 - (dc.embedding_vec <=> CAST(query_vector AS vector)) as similarity_score,
    dc.content
  FROM document_chunks dc
  WHERE dc.document_id = search_similar_chunks.document_id
    AND dc.has_embedding = true
    AND dc.embedding_vec IS NOT NULL
  ORDER BY dc.embedding_vec <=> CAST(query_vector AS vector)
  LIMIT limit_count;
END;
$$;

-- 3. Add index for faster vector searches (optional but recommended)
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks 
USING ivfflat (embedding_vec vector_cosine_ops)
WITH (lists = 100)
WHERE has_embedding = true;

-- 4. Grant execute permission (if needed)
GRANT EXECUTE ON FUNCTION search_similar_chunks(text, int, int) TO authenticated;
GRANT EXECUTE ON FUNCTION search_similar_chunks(text, int, int) TO anon;
GRANT EXECUTE ON FUNCTION search_similar_chunks(text, int, int) TO service_role;

