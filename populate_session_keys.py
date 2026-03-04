#!/usr/bin/env python
"""
Script to populate session_key field in existing QAConversationPair records
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import QAConversationPair

def populate_session_keys():
    """Populate session_key for existing QAConversationPair records"""
    
    print("🔄 Populating session_key for existing Q&A pairs...")
    
    # Get all Q&A pairs that don't have session_key populated
    qa_pairs_without_key = QAConversationPair.objects.filter(session_key__isnull=True) | QAConversationPair.objects.filter(session_key='')
    
    total_count = qa_pairs_without_key.count()
    print(f"📊 Found {total_count} Q&A pairs without session_key")
    
    if total_count == 0:
        print("✅ All Q&A pairs already have session_key populated!")
        return
    
    updated_count = 0
    for qa_pair in qa_pairs_without_key:
        if qa_pair.session and qa_pair.session.session_key:
            qa_pair.session_key = qa_pair.session.session_key
            qa_pair.save(update_fields=['session_key'])
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"   Updated {updated_count}/{total_count} records...")
        else:
            print(f"⚠️  Skipping Q&A pair {qa_pair.id} - no session or session_key found")
    
    print(f"✅ Successfully updated {updated_count} Q&A pairs with session_key")
    
    # Verify the update
    remaining_empty = QAConversationPair.objects.filter(session_key__isnull=True).count() + QAConversationPair.objects.filter(session_key='').count()
    if remaining_empty == 0:
        print("🎉 All Q&A pairs now have session_key populated!")
    else:
        print(f"⚠️  {remaining_empty} Q&A pairs still have empty session_key")

if __name__ == "__main__":
    populate_session_keys()
