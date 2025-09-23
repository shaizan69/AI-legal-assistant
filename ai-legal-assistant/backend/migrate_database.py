#!/usr/bin/env python3
"""
Database migration script to add Supabase columns
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add missing columns to the documents table"""
    
    # Find the database file
    db_path = Path("legal_assistant.db")
    if not db_path.exists():
        print("❌ Database file not found!")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔍 Checking current database schema...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Current columns: {columns}")
        
        # Add file_url column if it doesn't exist
        if 'file_url' not in columns:
            print("➕ Adding file_url column...")
            cursor.execute("ALTER TABLE documents ADD COLUMN file_url VARCHAR(1000)")
            print("✅ file_url column added")
        else:
            print("✅ file_url column already exists")
        
        # Add supabase_path column if it doesn't exist
        if 'supabase_path' not in columns:
            print("➕ Adding supabase_path column...")
            cursor.execute("ALTER TABLE documents ADD COLUMN supabase_path VARCHAR(500)")
            print("✅ supabase_path column added")
        else:
            print("✅ supabase_path column already exists")
        
        # Add description column if it doesn't exist
        if 'description' not in columns:
            print("➕ Adding description column...")
            cursor.execute("ALTER TABLE documents ADD COLUMN description TEXT")
            print("✅ description column added")
        else:
            print("✅ description column already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(documents)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated columns: {updated_columns}")
        
        conn.close()
        
        print("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
