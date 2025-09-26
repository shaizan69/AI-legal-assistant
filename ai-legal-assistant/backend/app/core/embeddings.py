"""
Embedding generation and vector database management
"""
import numpy as np
import logging
from typing import List, Optional, Tuple
from pathlib import Path

# Lazy imports to avoid startup delays
def _lazy_import_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None

def _lazy_import_faiss():
    try:
        import faiss
        return faiss
    except ImportError:
        return None

def _lazy_import_openai():
    try:
        import openai
        return openai
    except ImportError:
        return None

def _lazy_import_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except ImportError:
        return None

def _lazy_import_pinecone():
    try:
        from pinecone import Pinecone
        return Pinecone
    except ImportError:
        try:
            import pinecone
            return pinecone.init
        except ImportError:
            return None

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self.embedding_model = None
        self.vector_db = None
        self.dimension = None
        self._numpy = None
        self._faiss = None
        self._openai = None
        self._sentence_transformer = None
        self._pinecone = None
        self._initialize_embedding_model()
        self._initialize_vector_db()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        try:
            if settings.OPENAI_API_KEY:
                self._openai = _lazy_import_openai()
                if self._openai:
                    self._openai.api_key = settings.OPENAI_API_KEY
                    self.embedding_model = "openai"
                    self.dimension = 1536  # OpenAI ada-002 dimension
                    logger.info("Using OpenAI embeddings")
                else:
                    self.embedding_model = None
                    self.dimension = 384
                    logger.warning("OpenAI not available")
            else:
                # Try sentence transformers
                self._sentence_transformer = _lazy_import_sentence_transformers()
                if self._sentence_transformer:
                    # Use the model name directly (will download to D: drive cache)
                    self.embedding_model = self._sentence_transformer('all-MiniLM-L6-v2')
                    self.dimension = 384  # all-MiniLM-L6-v2 dimension
                    logger.info("Using HuggingFace sentence-transformers")
                else:
                    # No embedding model available
                    self.embedding_model = None
                    self.dimension = 384  # Default dimension
                    logger.warning("No embedding model available. Embedding features will be disabled.")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            self.embedding_model = None
            self.dimension = 384
            logger.warning("Failed to initialize embedding model. Embedding features will be disabled.")
    
    def _initialize_vector_db(self):
        """Initialize vector database"""
        try:
            if settings.VECTOR_DB_TYPE == "pinecone" and settings.PINECONE_API_KEY:
                self._pinecone = _lazy_import_pinecone()
                if self._pinecone:
                    pc = self._pinecone(api_key=settings.PINECONE_API_KEY)
                    self.vector_db = pc.Index("legal-documents")
                    logger.info("Using Pinecone vector database")
                else:
                    self.vector_db = self._load_or_create_faiss_index()
                    logger.info("Using FAISS vector database (Pinecone not available)")
            else:
                # Use FAISS
                self.vector_db = self._load_or_create_faiss_index()
                logger.info("Using FAISS vector database")
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            # Create a simple FAISS index as fallback
            self.vector_db = self._load_or_create_faiss_index()
            logger.warning("Using FAISS as fallback vector database")
    
    def _load_or_create_faiss_index(self):
        """Load existing FAISS index or create new one"""
        self._faiss = _lazy_import_faiss()
        if not self._faiss:
            logger.warning("FAISS not available, using dummy index")
            return None
            
        index_path = Path(settings.FAISS_INDEX_PATH)
        
        if index_path.exists():
            try:
                index = self._faiss.read_index(str(index_path))
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors")
                return index
            except Exception as e:
                logger.warning(f"Could not load existing FAISS index: {e}")
        
        # Create new index
        index = self._faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        logger.info("Created new FAISS index")
        return index
    
    def generate_embedding(self, text: str):
        """Generate embedding for a single text"""
        try:
            if self.embedding_model is None:
                logger.warning("No embedding model available. Returning zero vector.")
                self._numpy = _lazy_import_numpy()
                if self._numpy:
                    return self._numpy.zeros(self.dimension, dtype=self._numpy.float32)
                return [0.0] * self.dimension
            
            if self.embedding_model == "openai":
                if not self._openai:
                    self._openai = _lazy_import_openai()
                response = self._openai.embeddings.create(
                    input=text,
                    model=settings.EMBEDDING_MODEL
                )
                self._numpy = _lazy_import_numpy()
                if self._numpy:
                    return self._numpy.array(response.data[0].embedding, dtype=self._numpy.float32)
                return response.data[0].embedding
            else:
                # Use sentence-transformers
                embedding = self.embedding_model.encode(text, convert_to_tensor=False)
                self._numpy = _lazy_import_numpy()
                if self._numpy:
                    return embedding.astype(self._numpy.float32)
                return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            self._numpy = _lazy_import_numpy()
            if self._numpy:
                return self._numpy.zeros(self.dimension, dtype=self._numpy.float32)
            return [0.0] * self.dimension
    
    def generate_embeddings_batch(self, texts: List[str]):
        """Generate embeddings for multiple texts"""
        try:
            if self.embedding_model is None:
                logger.warning("No embedding model available. Returning zero vectors.")
                self._numpy = _lazy_import_numpy()
                if self._numpy:
                    return self._numpy.zeros((len(texts), self.dimension), dtype=self._numpy.float32)
                return [[0.0] * self.dimension for _ in texts]
            
            if self.embedding_model == "openai":
                if not self._openai:
                    self._openai = _lazy_import_openai()
                response = self._openai.embeddings.create(
                    input=texts,
                    model=settings.EMBEDDING_MODEL
                )
                self._numpy = _lazy_import_numpy()
                if self._numpy:
                    return self._numpy.array([data.embedding for data in response.data], dtype=self._numpy.float32)
                return [data.embedding for data in response.data]
            else:
                # Use sentence-transformers
                embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
                self._numpy = _lazy_import_numpy()
                if self._numpy:
                    return embeddings.astype(self._numpy.float32)
                return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            self._numpy = _lazy_import_numpy()
            if self._numpy:
                return self._numpy.zeros((len(texts), self.dimension), dtype=self._numpy.float32)
            return [[0.0] * self.dimension for _ in texts]
    
    def add_vectors(self, vectors: np.ndarray, ids: List[str], metadata: List[dict] = None):
        """Add vectors to the vector database"""
        try:
            if settings.VECTOR_DB_TYPE == "pinecone":
                # Prepare data for Pinecone
                vectors_to_upsert = []
                for i, (vector, doc_id) in enumerate(zip(vectors, ids)):
                    meta = metadata[i] if metadata else {}
                    vectors_to_upsert.append({
                        "id": doc_id,
                        "values": vector.tolist(),
                        "metadata": meta
                    })
                
                self.vector_db.upsert(vectors=vectors_to_upsert)
            else:
                # Use FAISS
                self.vector_db.add(vectors)
                self._save_faiss_index()
            
            logger.info(f"Added {len(vectors)} vectors to database")
        except Exception as e:
            logger.error(f"Error adding vectors: {e}")
            raise
    
    def search_similar(self, query_vector: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors"""
        try:
            if settings.VECTOR_DB_TYPE == "pinecone" and hasattr(self.vector_db, 'query'):
                results = self.vector_db.query(
                    vector=query_vector.tolist(),
                    top_k=k,
                    include_metadata=True
                )
                scores = [match.score for match in results.matches]
                ids = [match.id for match in results.matches]
                return np.array(scores), np.array(ids)
            else:
                # Use FAISS
                scores, indices = self.vector_db.search(query_vector.reshape(1, -1), k)
                return scores[0], indices[0]
        except Exception as e:
            logger.error(f"Error searching similar vectors: {e}")
            # Return empty results as fallback
            return np.array([]), np.array([])
    
    def _save_faiss_index(self):
        """Save FAISS index to disk"""
        try:
            index_path = Path(settings.FAISS_INDEX_PATH)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.vector_db, str(index_path))
            logger.info("FAISS index saved successfully")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
            raise
    
    def get_index_stats(self) -> dict:
        """Get vector database statistics"""
        try:
            if settings.VECTOR_DB_TYPE == "pinecone" and hasattr(self.vector_db, 'describe_index_stats'):
                stats = self.vector_db.describe_index_stats()
                return {
                    "total_vectors": stats.total_vector_count,
                    "dimension": stats.dimension,
                    "index_fullness": stats.index_fullness
                }
            else:
                return {
                    "total_vectors": self.vector_db.ntotal,
                    "dimension": self.vector_db.d,
                    "is_trained": self.vector_db.is_trained
                }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {
                "total_vectors": 0,
                "dimension": self.dimension,
                "is_trained": False
            }


# Global embedding service instance - use dummy for fast startup
class DummyEmbeddingService:
    def __init__(self):
        self.dimension = 384
        self.embedding_model = None
        self.vector_db = None
    
    def generate_embedding(self, text: str):
        return [0.0] * self.dimension
    
    def generate_embeddings_batch(self, texts: List[str]):
        return [[0.0] * self.dimension for _ in texts]
    
    def add_vectors(self, vectors, ids, metadata=None):
        pass
    
    def search_similar(self, query_vector, k=5):
        return [], []
    
    def get_index_stats(self):
        return {"total_vectors": 0, "dimension": self.dimension, "is_trained": False}

# Import Supabase embedding service
from app.core.supabase_embeddings import embedding_service
logger.info("Using lightweight embedding service for fast startup")
