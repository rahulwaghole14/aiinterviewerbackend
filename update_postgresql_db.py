#!/usr/bin/env python
"""
Script to update and test the new PostgreSQL database connection
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.conf import settings
from django.core.management import call_command

# New database URL
NEW_DATABASE_URL = "postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db"

print("=" * 60)
print("🔄 Updating PostgreSQL Database Configuration")
print("=" * 60)

# Test connection first
print("\n📡 Testing connection to new database...")
try:
    import psycopg2
    from urllib.parse import urlparse
    
    db_url = urlparse(NEW_DATABASE_URL)
    
    print(f"  Host: {db_url.hostname}")
    print(f"  Port: {db_url.port or 5432}")
    print(f"  Database: {db_url.path[1:]}")
    print(f"  User: {db_url.username}")
    
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
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n⚠️  Please ensure:")
    print("  1. Database is awake/resumed on Render.com")
    print("  2. Wait 1-2 minutes after resuming")
    print("  3. Check firewall/network settings")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Database connection verified!")
print("=" * 60)
print("\n📝 Next steps:")
print("  1. Update .env file with new DATABASE_URL")
print("  2. Set USE_POSTGRESQL = True in settings.py")
print("  3. Run: python manage.py migrate")
print("=" * 60)



