#!/usr/bin/env python3
"""
Test database configuration
"""

import sys
import os
sys.path.append('backend')

def test_database_config():
    """Test database configuration"""
    
    print("🔍 Testing Database Configuration...")
    
    try:
        from backend.app.core.config import settings
        print(f"📋 Database URL: {settings.DATABASE_URL}")
        
        if "sqlite+aiosqlite" in settings.DATABASE_URL:
            print("✅ SQLite async URL detected")
        else:
            print("❌ Wrong database URL format")
            return False
            
        # Test if we can create the async engine
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.DATABASE_URL)
        print("✅ Async engine created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_database_config()
