"""
Application configuration and settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
from pathlib import Path
from dotenv import dotenv_values  # type: ignore
import re


class Settings(BaseSettings):
    """Application settings with .env file support"""
    model_config = SettingsConfigDict(
        # Load env from project root (ai-legal-assistant/.env)
        env_file="D:/Legal assistant/ai-legal-assistant/.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Database - Supabase PostgreSQL (Transaction Mode for better connection handling)
    DATABASE_USER: str = "postgres.iuxqomqbxfoetnieaorw"
    DATABASE_PASSWORD: str = "SSr7304149910"
    DATABASE_HOST: str = "aws-1-ap-south-1.pooler.supabase.com"
    DATABASE_PORT: int = 6543
    DATABASE_NAME: str = "postgres"
    
    # AI Services
    # Embeddings use sentence-transformers locally
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # Groq API Configuration (Primary LLM)
    GROQ_API_KEY: str = ""
    # Default to groq/compound if not provided in env
    GROQ_MODEL: str = "groq/compound"
    GROQ_BASE_URL: str = ""
    
    # Legacy fields (unused)
    EMBEDDING_MODEL: str = ""
    LLM_MODEL: str = ""
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Configuration
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@yourdomain.com"
    SMTP_SERVER: str = "smtp.sendgrid.net"
    SMTP_PORT: int = 587
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File Upload
    UPLOAD_MAX_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "doc"]
    UPLOAD_DIR: str = "./uploads"
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET: str = "legal-documents"
    USE_SUPABASE: bool = True
    
    # Vector Database - Using Supabase PostgreSQL with pgvector
    VECTOR_DB_TYPE: str = "supabase"  # Using Supabase PostgreSQL with pgvector extension
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # Redis (Optional)
    REDIS_URL: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        
        # Set Hugging Face cache environment variables
        self._configure_huggingface_cache()
        
        # Remove OS env override for GROQ_MODEL so only .env file is authoritative
        try:
            if os.environ.get('GROQ_MODEL'):
                os.environ.pop('GROQ_MODEL', None)
        except Exception:
            pass

        # Force-read GROQ_MODEL from the main project .env to avoid OS env overrides
        main_env_path = "D:/Legal assistant/ai-legal-assistant/.env"
        file_model: Optional[str] = None
        # Try dotenv first
        try:
            main_env = dotenv_values(main_env_path)
            file_model = (main_env.get("GROQ_MODEL") or "").strip() if main_env else None
        except Exception:
            file_model = None
        # Fallback: manual parse
        if not file_model:
            try:
                with open(main_env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        m = re.match(r"\s*GROQ_MODEL\s*=\s*(.+)\s*$", line)
                        if m:
                            file_model = m.group(1).strip().strip('"').strip("'")
                            break
            except Exception:
                file_model = None
        if file_model:
            self.GROQ_MODEL = file_model
        # Log model selection for visibility
        try:
            print(f"[config] GROQ_MODEL loaded: {self.GROQ_MODEL}")
            print(f"[config] GROQ_API_KEY loaded: {self.GROQ_API_KEY[:10]}...")
            print(f"[config] Loading from env file: D:/Legal assistant/ai-legal-assistant/.env")
            print(f"[config] OS env GROQ_MODEL (cleared): {os.environ.get('GROQ_MODEL')}")
        except Exception as e:
            print(f"[config] Error logging model info: {e}")
    
    def _configure_huggingface_cache(self):
        """Configure Hugging Face cache directories to use D:\Hugging Face"""
        hf_home = os.environ.get('HF_HOME', 'D:\\Hugging Face')
        
        # Set environment variables for Hugging Face libraries
        os.environ['HF_HOME'] = hf_home
        os.environ['TRANSFORMERS_CACHE'] = os.path.join(hf_home, 'huggingface')
        os.environ['HF_HUB_CACHE'] = os.path.join(hf_home, 'huggingface')
        os.environ['HF_DATASETS_CACHE'] = os.path.join(hf_home, 'datasets')
        os.environ['TORCH_HOME'] = os.path.join(hf_home, 'torch')
        
        # Create cache directories if they don't exist
        for cache_dir in [
            os.environ['TRANSFORMERS_CACHE'],
            os.environ['HF_HUB_CACHE'],
            os.environ['HF_DATASETS_CACHE'],
            os.environ['TORCH_HOME']
        ]:
            os.makedirs(cache_dir, exist_ok=True)


# Global settings instance
settings = Settings()
