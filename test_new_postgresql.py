"""
Test the new PostgreSQL database connection
"""
import os
import sys
from urllib.parse import urlparse

# New database URL
NEW_DATABASE_URL = "postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db"

print("=" * 60)
print("🔍 Testing New PostgreSQL Database Connection")
print("=" * 60)

try:
    import psycopg2
    
    db_url = urlparse(NEW_DATABASE_URL)
    
    print(f"\n📡 Connection Details:")
    print(f"  Host: {db_url.hostname}")
    print(f"  Port: {db_url.port or 5432}")
    print(f"  Database: {db_url.path[1:]}")
    print(f"  User: {db_url.username}")
    
    print(f"\n🔄 Attempting connection...")
    conn = psycopg2.connect(
        host=db_url.hostname,
        port=db_url.port or 5432,
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        sslmode='require',
        connect_timeout=10
    )
    
    print("✅ Connection successful!")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ PostgreSQL Version: {version[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database is ready to use!")
    print("=" * 60)
    
except psycopg2.OperationalError as e:
    error_msg = str(e)
    print(f"\n❌ Connection failed: {error_msg}")
    
    if "SSL connection has been closed unexpectedly" in error_msg:
        print("\n⚠️  Database is PAUSED on Render.com")
        print("   Solution: Go to Render.com dashboard and wake up the database")
    elif "password authentication failed" in error_msg:
        print("\n⚠️  Authentication failed - check credentials")
    else:
        print(f"\n⚠️  Error: {error_msg}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

