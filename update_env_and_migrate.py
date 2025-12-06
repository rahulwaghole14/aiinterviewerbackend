#!/usr/bin/env python
"""
Script to update .env file with new PostgreSQL URL and run migrations
"""
import os
import re
from pathlib import Path

# New database URL
NEW_DATABASE_URL = "postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db"

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

print("=" * 60)
print("🔄 Updating .env file with new PostgreSQL URL")
print("=" * 60)

# Read current .env file
if ENV_FILE.exists():
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update DATABASE_URL
    if 'DATABASE_URL=' in content:
        # Replace existing DATABASE_URL
        content = re.sub(
            r'DATABASE_URL=.*',
            f'DATABASE_URL={NEW_DATABASE_URL}',
            content,
            flags=re.MULTILINE
        )
        print("✅ Updated DATABASE_URL")
    else:
        # Add DATABASE_URL if not exists
        content += f'\nDATABASE_URL={NEW_DATABASE_URL}\n'
        print("✅ Added DATABASE_URL")
    
    # Update USE_POSTGRESQL
    if 'USE_POSTGRESQL=' in content:
        content = re.sub(
            r'USE_POSTGRESQL=.*',
            'USE_POSTGRESQL=True',
            content,
            flags=re.MULTILINE
        )
        print("✅ Updated USE_POSTGRESQL=True")
    else:
        content += f'\nUSE_POSTGRESQL=True\n'
        print("✅ Added USE_POSTGRESQL=True")
    
    # Write back
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ .env file updated successfully!")
    print(f"   File: {ENV_FILE}")
else:
    # Create new .env file
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write(f'DATABASE_URL={NEW_DATABASE_URL}\n')
        f.write(f'USE_POSTGRESQL=True\n')
    print(f"✅ Created new .env file with PostgreSQL configuration")

print("\n" + "=" * 60)
print("📝 Next Steps:")
print("=" * 60)
print("1. Run migrations to create all tables:")
print("   python manage.py migrate")
print("\n2. Create admin user:")
print("   python manage.py create_admin")
print("\n3. Verify connection:")
print("   python test_new_postgresql.py")
print("=" * 60)

