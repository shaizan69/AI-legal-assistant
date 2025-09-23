"""
Supabase-based embedding service using pgvector (no OpenAI; local sentence-transformers only)
"""

import logging
import json
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

# OpenAI is intentionally not used in this project anymore

def _lazy_import_sentence_transformers():
    """Lazy import sentence transformers"""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except ImportError:
        return None

def _lazy_import_cross_encoder():
    """Lazy import CrossEncoder for reranking"""
    try:
        from sentence_transformers import CrossEncoder
        return CrossEncoder
    except ImportError:
        return None

class SupabaseEmbeddingService:
    """Embedding service using Supabase PostgreSQL with pgvector"""
    
    def __init__(self):
        self.embedding_model = None
        self.dimension = None
        self._sentence_transformer = None
        self._cross_encoder = None
        self._reranker = None
        self.uses_e5 = False
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        try:
            # Initialize sentence-transformers
            self._sentence_transformer = _lazy_import_sentence_transformers()
            if self._sentence_transformer:
                # Switch to intfloat/e5-large-v2 (1024-dim)
                self.embedding_model = self._sentence_transformer('intfloat/e5-large-v2')
                self.dimension = 1024
                self.uses_e5 = True
                logger.info("Using e5-large-v2 embeddings with Supabase")

                # Initialize a lightweight CrossEncoder reranker
                self._cross_encoder = _lazy_import_cross_encoder()
                if self._cross_encoder:
                    try:
                        # Small, fast reranker. Swap to a larger model if you prefer.
                        self._reranker = self._cross_encoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                        logger.info("CrossEncoder reranker initialized: ms-marco-MiniLM-L-6-v2")
                    except Exception as e:
                        logger.warning(f"Failed to initialize CrossEncoder reranker: {e}")
            else:
                self.embedding_model = None
                self.dimension = 384
                logger.warning("No embedding model available; embeddings disabled")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            self.embedding_model = None
            self.dimension = 384
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.embedding_model:
            logger.warning("No embedding model available")
            return [0.0] * self.dimension
        
        try:
            # Sentence transformers only
            input_text = f"query: {text}" if self.uses_e5 else text
            embedding = self.embedding_model.encode(input_text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.dimension
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.embedding_model:
            logger.warning("No embedding model available")
            return [[0.0] * self.dimension for _ in texts]
        
        try:
            # Sentence transformers only
            batched_texts = [f"passage: {t}" for t in texts] if self.uses_e5 else texts
            embeddings = self.embedding_model.encode(batched_texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * self.dimension for _ in texts]
    
    def add_vectors(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict] = None):
        """Add vectors to Supabase PostgreSQL using pgvector"""
        if not vectors or not ids:
            return
        
        try:
            db = next(get_db())
            
            # Prepare data for batch upsert based on document_id + chunk_index
            for i, (vector, vector_id) in enumerate(zip(vectors, ids)):
                # Convert vector to pgvector format
                vector_str = f"[{','.join(map(str, vector))}]"
                
                # Extract metadata
                meta = metadata[i] if metadata and i < len(metadata) else {}
                
                # Insert or update vector in document_chunks table
                # Upsert by natural key (document_id, chunk_index)
                query = text("""
                    INSERT INTO document_chunks (embedding, embedding_vec, has_embedding, document_id, chunk_index, content, metadata)
                    VALUES (:embedding, CAST(:embedding AS vector), :has_embedding, :document_id, :chunk_index, :content, :metadata)
                    ON CONFLICT (document_id, chunk_index)
                    DO UPDATE SET 
                        embedding = EXCLUDED.embedding,
                        embedding_vec = EXCLUDED.embedding_vec,
                        has_embedding = EXCLUDED.has_embedding,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata
                """)
                
                db.execute(query, {
                    'embedding': vector_str,
                    'has_embedding': True,
                    'document_id': meta.get('document_id'),
                    'chunk_index': meta.get('chunk_index', 0),
                    'content': meta.get('content', ''),
                    'metadata': json.dumps(meta)
                })
            
            db.commit()
            logger.info(f"Added {len(vectors)} vectors to Supabase")
            
        except Exception as e:
            logger.error(f"Error adding vectors to Supabase: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    def search_similar(self, query_vector: List[float], k: int = 5, document_id: Optional[int] = None, question_text: Optional[str] = None) -> Tuple[List[str], List[float]]:
        """Search for similar vectors using pgvector"""
        if not query_vector:
            return [], []
        
        try:
            db = next(get_db())
            
            # Convert query vector to pgvector format
            query_vector_str = f"[{','.join(map(str, query_vector))}]"
            
            # Build query with optional document filter
            where_clause = ""
            # Retrieve a larger candidate set for reranking
            candidate_k = max(k * 6, 50)
            params = {'query_vector': query_vector_str, 'limit': candidate_k}
            
            if document_id:
                where_clause = "WHERE document_id = :document_id"
                params['document_id'] = document_id
            
            # Ensure correct WHERE/AND combination for has_embedding filter
            has_filter = "AND has_embedding = true" if where_clause else "WHERE has_embedding = true"

            query = text(f"""
                SELECT 
                    content,
                    document_id,
                    chunk_index,
                    1 - (embedding_vec <=> CAST(:query_vector AS vector)) as similarity_score
                FROM document_chunks 
                {where_clause}
                {has_filter}
                ORDER BY embedding_vec <=> CAST(:query_vector AS vector)
                LIMIT :limit
            """)
            
            result = db.execute(query, params)
            rows = result.fetchall()

            if not rows:
                return [], []

            # Optional reranking with CrossEncoder
            if self._reranker:
                try:
                    # Build (query, passage) pairs using the real question text when available
                    q = question_text or " ".join(str(x) for x in query_vector[:16])
                    pairs = [(q, row.content) for row in rows]
                    scores_ce = self._reranker.predict(pairs)
                    ranked = sorted(zip(rows, scores_ce), key=lambda x: x[1], reverse=True)[:k]
                    top_rows = [r for (r, _) in ranked]
                except Exception as e:
                    logger.warning(f"Reranker failed, falling back to vector order: {e}")
                    top_rows = rows[:k]
            else:
                top_rows = rows[:k]

            ids = [f"doc_{row.document_id}_chunk_{row.chunk_index}" for row in top_rows]
            # If reranked, similarity_score no longer matches true distance; return placeholder ranks
            scores = [getattr(row, 'similarity_score', 0.0) for row in top_rows]
            logger.info(f"Found {len(ids)} similar vectors (post-rerank)")
            return ids, scores
            
        except Exception as e:
            logger.error(f"Error searching similar vectors: {e}")
            return [], []
        finally:
            if 'db' in locals():
                db.close()
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        try:
            db = next(get_db())
            
            # Count total vectors
            count_query = text("SELECT COUNT(*) as total FROM document_chunks WHERE has_embedding = true")
            result = db.execute(count_query)
            total_vectors = result.fetchone().total
            
            # Get dimension info
            dimension_query = text("""
                SELECT array_length(string_to_array(embedding, ','), 1) as dimension 
                FROM document_chunks 
                WHERE has_embedding = true 
                LIMIT 1
            """)
            result = db.execute(dimension_query)
            row = result.fetchone()
            dimension = row.dimension if row else self.dimension
            
            return {
                "total_vectors": total_vectors,
                "dimension": dimension,
                "is_trained": total_vectors > 0,
                "database_type": "supabase_pgvector"
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {
                "total_vectors": 0,
                "dimension": self.dimension,
                "is_trained": False,
                "database_type": "supabase_pgvector"
            }
        finally:
            if 'db' in locals():
                db.close()

# Global embedding service instance
embedding_service = SupabaseEmbeddingService()
