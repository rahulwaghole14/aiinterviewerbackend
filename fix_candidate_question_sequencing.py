#!/usr/bin/env python
"""
Script to fix candidate question sequencing to use 1000+ numbering
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import QAConversationPair

def fix_candidate_question_sequencing():
    """Fix candidate questions to use 1000+ numbering"""
    
    print("🔄 Fixing candidate question sequencing...")
    
    # Get all candidate questions
    candidate_questions = QAConversationPair.objects.filter(
        question_type='CANDIDATE_QUESTION'
    ).order_by('pdf_display_order')
    
    total_count = candidate_questions.count()
    print(f"📊 Found {total_count} candidate questions to resequence")
    
    if total_count == 0:
        print("✅ No candidate questions found!")
        return
    
    updated_count = 0
    # Assign 1000+ numbers in chronological order
    for i, qa_pair in enumerate(candidate_questions):
        # Calculate 1000+ number (first gets 1000, then 1001, etc.)
        new_question_number = 1000 + i
        
        if qa_pair.question_number != new_question_number:
            qa_pair.question_number = new_question_number
            qa_pair.save(update_fields=['question_number'])
            updated_count += 1
            
            print(f"   Updated Q&A pair {qa_pair.id}: {qa_pair.question_number} -> {new_question_number}")
    
    print(f"✅ Successfully updated {updated_count} candidate questions")
    
    # Verify the update
    print("\n🔍 Verification:")
    for qa in QAConversationPair.objects.filter(question_type='CANDIDATE_QUESTION').order_by('question_number'):
        print(f"   Q#{qa.question_number}: {qa.answer_text[:50]}...")

if __name__ == "__main__":
    fix_candidate_question_sequencing()
