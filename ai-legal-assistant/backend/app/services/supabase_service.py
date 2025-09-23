"""
Supabase service for file storage and management
"""

import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase Storage"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.bucket = settings.SUPABASE_BUCKET
        
        if settings.USE_SUPABASE and settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase not configured or disabled")
    
    def is_available(self) -> bool:
        """Check if Supabase service is available"""
        return self.client is not None
    
    async def upload_file(self, file_path: str, file_content: bytes, content_type: str = "application/octet-stream") -> Optional[dict]:
        """Upload file to Supabase Storage"""
        if not self.is_available():
            logger.error("Supabase service not available")
            return None
        
        try:
            # Upload file to Supabase Storage
            result = self.client.storage.from_(self.bucket).upload(
                path=file_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600"
                }
            )
            
            if result.get('error'):
                logger.error(f"Supabase upload error: {result['error']}")
                return None
            
            logger.info(f"File uploaded to Supabase: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            return None
    
    async def get_file_url(self, file_path: str) -> Optional[str]:
        """Get public URL for a file in Supabase Storage"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.storage.from_(self.bucket).get_public_url(file_path)
            # get_public_url returns a dict with 'publicURL' key
            if isinstance(result, dict) and 'publicURL' in result:
                return result['publicURL']
            elif isinstance(result, str):
                return result
            else:
                logger.error(f"Unexpected result from get_public_url: {result}")
                return None
        except Exception as e:
            logger.error(f"Error getting file URL from Supabase: {e}")
            return None
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        """Download file content from Supabase Storage"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.storage.from_(self.bucket).download(file_path)
            
            if result is None:
                logger.error(f"File not found in Supabase: {file_path}")
                return None
            
            logger.info(f"File downloaded from Supabase: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error downloading file from Supabase: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase Storage"""
        if not self.is_available():
            return False
        
        try:
            result = self.client.storage.from_(self.bucket).remove([file_path])
            
            if result.get('error'):
                logger.error(f"Supabase delete error: {result['error']}")
                return False
            
            logger.info(f"File deleted from Supabase: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {e}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in Supabase Storage"""
        if not self.is_available():
            return False
        
        try:
            result = self.client.storage.from_(self.bucket).list(path=file_path)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking file existence in Supabase: {e}")
            return False

# Global instance
supabase_service = SupabaseService()
