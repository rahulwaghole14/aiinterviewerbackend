#!/usr/bin/env python
"""
Check database schema for InterviewQuestion
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from django.db import connection

def check_schema():
    """Check the database schema"""
    
    print("=== Checking InterviewQuestion Schema ===\n")
    
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(interview_app_interviewquestion)")
        columns = cursor.fetchall()
        
        print("📋 InterviewQuestion Table Columns:")
        for col in columns:
            print(f"   {col[1]} ({col[2]}) - NOT NULL: {col[3]} - DEFAULT: {col[4]}")
        
        print(f"\n🔍 Looking for 'asked_at' field:")
        asked_at_found = False
        for col in columns:
            if 'asked_at' in col[1]:
                asked_at_found = True
                print(f"   ✅ Found: {col[1]} ({col[2]})")
        
        if not asked_at_found:
            print(f"   ❌ 'asked_at' field NOT found in table")
            
        print(f"\n🔍 Looking for 'answered_at' field:")
        answered_at_found = False
        for col in columns:
            if 'answered_at' in col[1]:
                answered_at_found = True
                print(f"   ✅ Found: {col[1]} ({col[2]})")
        
        if not answered_at_found:
            print(f"   ❌ 'answered_at' field NOT found in table")
            
        print(f"\n🔍 Looking for 'created_at' field:")
        created_at_found = False
        for col in columns:
            if 'created_at' in col[1]:
                created_at_found = True
                print(f"   ✅ Found: {col[1]} ({col[2]})")
        
        if not created_at_found:
            print(f"   ❌ 'created_at' field NOT found in table")

if __name__ == "__main__":
    check_schema()
