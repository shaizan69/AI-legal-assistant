"""
Database configuration and connection management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
import logging
from typing import AsyncGenerator

from app.core.config import settings

logger = logging.getLogger(__name__)

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}?sslmode=require"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

# Create async engine for async operations
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    poolclass=NullPool,
    connect_args={
        # PGBouncer (transaction/statement mode) does not support prepared statements
        # asyncpg: disable client-side prepared statement cache
        "statement_cache_size": 0,
        # asyncpg: disable server-side prepared statement cache
        "prepared_statement_cache_size": 0
    }
)

# Create sync engine for sync operations with robust connection handling
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    connect_args={
        "connect_timeout": 60,  # 60 seconds connection timeout
        "application_name": "legal_assistant_backend",
        "options": "-c statement_timeout=120000"  # 2 minutes statement timeout
    },
    # Add retry logic for connection failures
    pool_reset_on_return='commit'
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables using sync engine to avoid asyncpg + pgbouncer prepared statements."""
    import time
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Import all models to ensure they are registered
            from app.models import user, document, analysis

            # Use sync engine for DDL to avoid asyncpg prepared statements under pgbouncer
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")

            # Ensure pgvector extension and vector column exist, and migrate data
            from sqlalchemy import text
            with engine.begin() as conn:
                # Enable pgvector
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

                # Check if vector column already exists before adding
                result = conn.execute(text(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' 
                    AND column_name = 'embedding_vec'
                    """
                )).fetchone()
                
                if not result:
                    # Add vector column if missing (adjust to 384 for all-MiniLM-L6-v2)
                    logger.info("Adding embedding_vec column to document_chunks table...")
                    conn.execute(text(
                        """
                        ALTER TABLE document_chunks
                        ADD COLUMN embedding_vec vector(384)
                        """
                    ))
                    logger.info("embedding_vec column added successfully")
                else:
                    logger.info("embedding_vec column already exists")

                # Backfill embedding_vec from existing text embeddings when null (with limit for performance)
                # Convert comma-separated text to float4[] then to vector
                logger.info("Checking for existing embeddings to backfill...")
                count_result = conn.execute(text(
                    """
                    SELECT COUNT(*) 
                    FROM document_chunks 
                    WHERE embedding_vec IS NULL AND embedding IS NOT NULL AND embedding <> ''
                    """
                )).fetchone()
                
                if count_result and count_result[0] > 0:
                    logger.info(f"Found {count_result[0]} embeddings to backfill. Processing in batches...")
                    # Process in smaller batches to avoid timeout
                    conn.execute(text(
                        """
                        UPDATE document_chunks
                        SET embedding_vec = (string_to_array(embedding, ',')::real[])::vector
                        WHERE embedding_vec IS NULL AND embedding IS NOT NULL AND embedding <> ''
                        AND id IN (
                            SELECT id FROM document_chunks 
                            WHERE embedding_vec IS NULL AND embedding IS NOT NULL AND embedding <> ''
                            LIMIT 1000
                        )
                        """
                    ))
                    logger.info("Batch backfill completed")
                else:
                    logger.info("No embeddings need backfilling")

                # Ensure metadata column exists for chunks
                metadata_result = conn.execute(text(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' 
                    AND column_name = 'metadata'
                    """
                )).fetchone()
                
                if not metadata_result:
                    logger.info("Adding metadata column to document_chunks table...")
                    conn.execute(text(
                        """
                        ALTER TABLE document_chunks
                        ADD COLUMN metadata jsonb
                        """
                    ))
                    logger.info("metadata column added successfully")
                else:
                    logger.info("metadata column already exists")

                # Ensure a unique index exists for upserts on (document_id, chunk_index)
                conn.execute(text(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_document_chunks_doc_chunk
                    ON document_chunks (document_id, chunk_index)
                    """
                ))
            logger.info("pgvector ensured and embedding_vec backfilled where possible")
            return  # Success, exit retry loop
            
        except Exception as e:
            logger.warning(f"Database initialization attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database initialization failed after {max_retries} attempts: {e}")
                raise


def check_db_connection():
    """Check database connection with retry logic"""
    import time
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                return False
