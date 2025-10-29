-- Verification queries to check if vector search setup is complete
-- Run each section separately to verify

-- 1. Check if pgvector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 2. Check if the search function exists
SELECT 
  routine_name,
  routine_type,
  data_type
FROM information_schema.routines
WHERE routine_name = 'search_similar_chunks';

-- 3. Check if the embedding_vec column exists
SELECT 
  column_name,
  data_type,
  udt_name
FROM information_schema.columns
WHERE table_name = 'document_chunks' 
  AND column_name = 'embedding_vec';

-- 4. Check if the index exists
SELECT 
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename = 'document_chunks'
  AND indexname = 'document_chunks_embedding_idx';

-- 5. Check function permissions
SELECT 
  routine_name,
  grantee,
  privilege_type
FROM information_schema.routine_privileges
WHERE routine_name = 'search_similar_chunks';

