"""
Test PostgreSQL database connection
Run this to diagnose connection issues
"""
import os
import sys
from pathlib import Path

# Load environment
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")
except:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not found in environment")
    sys.exit(1)

print(f"[INFO] DATABASE_URL found: {DATABASE_URL[:50]}...")
print(f"[INFO] Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'N/A'}")

# Test basic connection
try:
    import psycopg2
    from urllib.parse import urlparse
    
    db_url = urlparse(DATABASE_URL)
    
    print(f"\n[TEST] Attempting connection...")
    print(f"  Host: {db_url.hostname}")
    print(f"  Port: {db_url.port or 5432}")
    print(f"  Database: {db_url.path[1:]}")
    print(f"  User: {db_url.username}")
    
    # Try connection with SSL
    conn = psycopg2.connect(
        host=db_url.hostname,
        port=db_url.port or 5432,
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        sslmode='require',
        connect_timeout=10
    )
    
    print("[SUCCESS] Connection successful!")
    conn.close()
    
except psycopg2.OperationalError as e:
    error_msg = str(e)
    print(f"\n[ERROR] Connection failed: {error_msg}")
    
    if "SSL connection has been closed unexpectedly" in error_msg:
        print("\n[SOLUTION] This usually means:")
        print("  1. Render.com database is PAUSED (free tier pauses after inactivity)")
        print("  2. Go to Render.com dashboard and wake up/resume the database")
        print("  3. Wait 1-2 minutes after resuming before retrying")
        print("  4. Or upgrade to a paid plan for always-on database")
    elif "could not translate host name" in error_msg:
        print("\n[SOLUTION] DNS/Network issue:")
        print("  1. Check your internet connection")
        print("  2. Verify the database hostname is correct")
        print("  3. Check firewall/VPN settings")
    elif "password authentication failed" in error_msg:
        print("\n[SOLUTION] Authentication failed:")
        print("  1. Verify DATABASE_URL credentials are correct")
        print("  2. Check if password has special characters that need encoding")
    else:
        print(f"\n[SOLUTION] Check the error message above for details")
        
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

