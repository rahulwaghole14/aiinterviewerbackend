#!/usr/bin/env python
"""
Script to test PostgreSQL database connection from .env file.
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception as e:
    print(f"⚠️  Could not load dotenv: {e}")

django.setup()

from django.db import connection
from django.conf import settings

def test_postgres_connection():
    """Test PostgreSQL database connection"""
    print("=" * 60)
    print("🔍 Testing PostgreSQL Database Connection")
    print("=" * 60)
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get("DATABASE_URL", "")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please check your .env file")
        return False
    
    print(f"\n📋 DATABASE_URL: {database_url[:50]}..." if len(database_url) > 50 else f"\n📋 DATABASE_URL: {database_url}")
    
    # Check database configuration
    db_config = settings.DATABASES.get('default', {})
    print(f"\n📊 Database Configuration:")
    print(f"   Engine: {db_config.get('ENGINE', 'Not set')}")
    print(f"   Name: {db_config.get('NAME', 'Not set')}")
    print(f"   Host: {db_config.get('HOST', 'Not set')}")
    print(f"   Port: {db_config.get('PORT', 'Not set')}")
    print(f"   User: {db_config.get('USER', 'Not set')}")
    
    # Test connection
    try:
        print(f"\n🔌 Attempting to connect to database...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL Version: {version[0]}")
            
            # Test a simple query
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            print(f"   Current Database: {db_info[0]}")
            print(f"   Current User: {db_info[1]}")
            
            # Check if we can query tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                LIMIT 5;
            """)
            tables = cursor.fetchall()
            if tables:
                print(f"\n📋 Sample tables found: {len(tables)}")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print(f"\n📋 No tables found (database might be empty)")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"   Error: {str(e)}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Check if DATABASE_URL is correct in .env file")
        print(f"   2. Verify database credentials")
        print(f"   3. Check if database server is accessible")
        print(f"   4. Ensure database exists")
        return False

if __name__ == "__main__":
    try:
        success = test_postgres_connection()
        print("\n" + "=" * 60)
        if success:
            print("✅ Database connection test completed successfully!")
        else:
            print("❌ Database connection test failed!")
        print("=" * 60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

