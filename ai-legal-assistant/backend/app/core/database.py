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

# Create sync engine for sync operations
# If using Transaction Pooler or Session Pooler, we want to ensure we disable SQLAlchemy client side pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
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

            # Add vector column if missing (adjust to 1024 for e5-large-v2)
            conn.execute(text(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS embedding_vec vector(1024)
                """
            ))

            # Backfill embedding_vec from existing text embeddings when null
            # Convert comma-separated text to float4[] then to vector
            conn.execute(text(
                """
                UPDATE document_chunks
                SET embedding_vec = (string_to_array(embedding, ',')::real[])::vector
                WHERE embedding_vec IS NULL AND embedding IS NOT NULL AND embedding <> ''
                """
            ))

            # Ensure metadata column exists for chunks
            conn.execute(text(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS metadata jsonb
                """
            ))

            # Ensure a unique index exists for upserts on (document_id, chunk_index)
            conn.execute(text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_document_chunks_doc_chunk
                ON document_chunks (document_id, chunk_index)
                """
            ))
        logger.info("pgvector ensured and embedding_vec backfilled where possible")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def check_db_connection():
    """Check database connection"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
