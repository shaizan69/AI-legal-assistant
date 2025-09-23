#!/usr/bin/env python3
"""
Test configuration loading
"""

import sys
import os
sys.path.append('backend')

from backend.app.core.config import settings

def test_config():
    """Test if configuration is loaded properly"""
    
    print("🔍 Testing Configuration Loading...")
    
    print(f"📋 Supabase URL: {settings.SUPABASE_URL}")
    print(f"📋 Supabase Key: {'Set' if settings.SUPABASE_KEY else 'Not Set'}")
    print(f"📋 Use Supabase: {settings.USE_SUPABASE}")
    print(f"📋 Groq API Key: {'Set' if settings.GROQ_API_KEY else 'Not Set'}")
    print(f"📋 Groq Model: {settings.GROQ_MODEL}")
    
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        print("✅ Supabase configuration loaded successfully")
    else:
        print("❌ Supabase configuration missing")
    
    if settings.GROQ_API_KEY:
        print("✅ Groq configuration loaded successfully")
    else:
        print("❌ Groq configuration missing")
    
    return settings.SUPABASE_URL and settings.SUPABASE_KEY and settings.GROQ_API_KEY

if __name__ == "__main__":
    test_config()
