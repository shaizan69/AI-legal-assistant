#!/usr/bin/env python3
"""
Test script for login functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_async_db, init_db
from app.core.utils import verify_password, get_password_hash
from app.models.user import User
from sqlalchemy import select

async def test_login():
    """Test login functionality"""
    try:
        print("Testing login functionality...")
        
        # Initialize database
        await init_db()
        print("✓ Database initialized")
        
        # Get database session
        async for db in get_async_db():
            # Check if user exists
            result = await db.execute(
                select(User).filter(User.email == "test@example.com")
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✓ User found: {user.email}")
                print(f"✓ User active: {user.is_active}")
                print(f"✓ Hashed password: {user.hashed_password[:20]}...")
                
                # Test password verification
                is_valid = verify_password("testpass", user.hashed_password)
                print(f"✓ Password verification: {is_valid}")
                
                if is_valid:
                    print("✓ Login should work!")
                else:
                    print("✗ Password verification failed")
            else:
                print("✗ User not found")
                
            break
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login())
