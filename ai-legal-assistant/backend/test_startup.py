#!/usr/bin/env python3
"""
Test server startup
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_startup():
    """Test if the application can start"""
    
    print("🔍 Testing Application Startup...")
    
    try:
        print("1. Testing config import...")
        from app.core.config import settings
        print(f"   ✅ Config loaded - DB URL: {settings.DATABASE_URL}")
        
        print("2. Testing database import...")
        from app.core.database import async_engine, engine
        print("   ✅ Database engines created")
        
        print("3. Testing models import...")
        from app.models import user, document, analysis
        print("   ✅ Models imported")
        
        print("4. Testing main app import...")
        from app.main import app
        print("   ✅ FastAPI app created")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_startup()
