#!/usr/bin/env python3
"""
Debug login functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_async_db, init_db
from app.core.utils import verify_password, get_password_hash, create_access_token
from app.models.user import User
from sqlalchemy import select
from datetime import datetime, timedelta
from app.core.config import settings

async def debug_login():
    """Debug login functionality step by step"""
    try:
        print("=== Debug Login Process ===")
        
        # Initialize database
        await init_db()
        print("✓ Database initialized")
        
        # Get database session
        async for db in get_async_db():
            print("✓ Got database session")
            
            # Find user
            result = await db.execute(
                select(User).filter(User.email == "test@example.com")
            )
            user = result.scalar_one_or_none()
            print(f"✓ User query result: {user is not None}")
            
            if user:
                print(f"✓ User found: {user.email}")
                print(f"✓ User active: {user.is_active}")
                print(f"✓ User password hash: {user.hashed_password[:30]}...")
                
                # Test password verification
                password = "testpass"
                is_valid = verify_password(password, user.hashed_password)
                print(f"✓ Password verification: {is_valid}")
                
                if is_valid and user.is_active:
                    print("✓ User validation passed")
                    
                    # Update last login
                    user.last_login = datetime.utcnow()
                    await db.commit()
                    print("✓ Last login updated")
                    
                    # Create access token
                    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    access_token = create_access_token(
                        data={"sub": user.email}, expires_delta=access_token_expires
                    )
                    print(f"✓ Access token created: {access_token[:30]}...")
                    
                    # Return token data
                    token_data = {
                        "access_token": access_token,
                        "token_type": "bearer",
                        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                    }
                    print(f"✓ Token data: {token_data}")
                    print("✓ Login process completed successfully!")
                    
                else:
                    print("✗ User validation failed")
            else:
                print("✗ User not found")
                
            break
            
    except Exception as e:
        print(f"✗ Error in debug_login: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_login())
