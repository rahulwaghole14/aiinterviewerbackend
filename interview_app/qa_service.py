from .models import TechnicalInterviewQA, InterviewQuestion

def update_technical_qa_summary(session):
    """
    Update the TechnicalInterviewQA table for a session.
    Aggregates all TECHNICAL questions and answers into a single continuous text block
    and stores it in a single row in TechnicalInterviewQA.
    """
    # Fetch all technical/behavioral questions/answers for this session
    # Order by 'order' primarily, and 'created_at' secondarily to ensure correct sequence for items with same order
    from django.db.models import Q
    
    questions = InterviewQuestion.objects.filter(
        session=session
    ).filter(
        Q(question_type='TECHNICAL') | Q(question_type='BEHAVIORAL')
    ).order_by('order', 'conversation_sequence', 'id')
    
    # Construct the continuous text with newlines
    qa_lines = []
    
    processed_orders = set()
    for q in questions:
        ord_key = q.order
        role = (q.role or '').upper()
        
        # Simple deduplication: only process each (order, role) pair once
        if (ord_key, role) in processed_orders and role != '':
            continue
        processed_orders.add((ord_key, role))
        
        is_legacy = q.role is None
        
        # --- Handle AI Content ---
        if is_legacy or role == 'AI' or role == 'AI_RESPONSE':
            if q.question_text:
                q_text = q.question_text.strip()
                if q_text.startswith("Q:"): q_text = q_text[2:].strip()
                if q_text.startswith("AI Interviewer:"): q_text = q_text.replace("AI Interviewer:", "").strip()
                qa_lines.append(f"AI Interviewer: {q_text}")
        
        # --- Handle Interviewee Content ---
        if is_legacy or role == 'INTERVIEWEE' or role == 'CANDIDATE_QUESTION':
            if q.transcribed_answer:
                a_text = q.transcribed_answer.strip()
                if a_text.startswith("A:"): a_text = a_text[2:].strip()
                if a_text.startswith("Q:"): a_text = a_text[2:].strip()
                qa_lines.append(f"Interviewee: {a_text}")

    if not qa_lines:
        return # Nothing to save
        
    # Join with newlines to form the final continuous string
    overall_qa_text = "\n".join(qa_lines)
    
    # Update or Create the single row for this session
    TechnicalInterviewQA.objects.update_or_create(
        session=session,
        defaults={'overall_qa': overall_qa_text}
    )
    print(f"✅ Updated TechnicalInterviewQA for session {session.id} with {len(qa_lines)} lines.")
