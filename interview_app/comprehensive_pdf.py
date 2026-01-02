"""
Comprehensive PDF generation including Q&A and Coding Round results
Uses fpdf2 for PDF generation
"""
# Import FPDF at module level with fallback
FPDF = None
try:
    from fpdf2 import FPDF as FPDF2
    FPDF = FPDF2
    print("✅ Using fpdf2 for comprehensive PDF generation")
except ImportError as e:
    print(f"❌ fpdf2 import failed: {e}")
    try:
        # Fallback to fpdf (older package)
        from fpdf import FPDF as FPDF1
        FPDF = FPDF1
        print("✅ Using fpdf (fallback) for comprehensive PDF generation")
    except ImportError as e2:
        print(f"❌ fpdf import also failed: {e2}")
        print("   Please ensure fpdf2 is installed: pip install fpdf2")
        import traceback
        traceback.print_exc()

from .models import InterviewSession, CodeSubmission


def _sanitize_for_pdf(text: str) -> str:
    """Sanitize text for PDF encoding"""
    try:
        return text.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return text


def _wrap_long_words(text: str, max_len: int = 50) -> str:
    """Wrap long words to prevent PDF overflow - more aggressive wrapping"""
    if not text:
        return ""
    
    parts = []
    for token in text.split(' '):
        if len(token) <= max_len:
            parts.append(token)
        else:
            # Break very long tokens into smaller chunks
            for i in range(0, len(token), max_len):
                chunk = token[i:i+max_len]
                parts.append(chunk)
    
    result = ' '.join(parts)
    
    # Additional safety: if result is still too long, truncate it
    if len(result) > 10000:
        result = result[:10000] + "... (truncated)"
    
    return result


def _wrap_text_for_pdf(text: str, max_width: int = 70) -> str:
    """Wrap text to fit within PDF page width, breaking at word boundaries"""
    if not text:
        return ""
    
    words = text.split(' ')
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        # If adding this word would exceed max_width, start a new line
        if current_length + word_length + 1 > max_width and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            current_line.append(word)
            current_length += word_length + 1
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)


def _format_analysis_text(analysis_text: str) -> list:
    """
    Parse analysis text and format it with bullets, bold headings, and numbered lists.
    Returns a list of formatted lines with formatting instructions.
    Each item is a dict: {'type': 'bold'|'bullet'|'number'|'normal', 'text': str, 'level': int}
    """
    if not analysis_text:
        return []
    
    formatted_lines = []
    lines = analysis_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Detect section headings (ALL CAPS or Title Case ending with colon)
        if (line.endswith(':') and len(line) < 60 and not line[0].isdigit()) or \
           (line.isupper() and len(line) < 80 and not line.startswith('•')):
            formatted_lines.append({'type': 'bold', 'text': line, 'level': 0})
        
        # Detect numbered lists (1., 2., etc. or 1) 2) etc.)
        elif line and len(line) > 2 and line[0].isdigit() and line[1] in ['.', ')']:
            # Extract number and text
            num_end = 2 if line[1] == '.' else 3
            number = line[:num_end]
            text = line[num_end:].strip()
            # Remove leading dash or bullet if present
            if text.startswith('-') or text.startswith('•'):
                text = text[1:].strip()
            formatted_lines.append({'type': 'number', 'text': text, 'number': number})
        
        # Detect bullet points (-, *, •)
        elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
            text = line[1:].strip()
            # Check if it's a sub-bullet (starts with space before bullet)
            level = 1 if lines[i].startswith('  ') or lines[i].startswith('\t') else 0
            formatted_lines.append({'type': 'bullet', 'text': text, 'level': level})
        
        # Detect sub-bullets (indented with spaces or tabs)
        elif (line.startswith('  ') or line.startswith('\t')) and len(line) > 2:
            text = line.strip()
            if text.startswith('-') or text.startswith('*') or text.startswith('•'):
                text = text[1:].strip()
            formatted_lines.append({'type': 'bullet', 'text': text, 'level': 1})
        
        # Regular text (but check if it looks like a heading)
        else:
            # If line is short and looks like a heading, make it bold
            if len(line) < 60 and (line.isupper() or (line[0].isupper() and ':' in line)):
                formatted_lines.append({'type': 'bold', 'text': line, 'level': 0})
            else:
                formatted_lines.append({'type': 'normal', 'text': line, 'level': 0})
        
        i += 1
    
    return formatted_lines


def generate_comprehensive_pdf(session_key: str) -> bytes:
    """
    Generate comprehensive PDF including:
    - Technical Q&A transcript
    - Coding challenge results
    - AI evaluation
    """
    # Try to import FPDF at runtime if not already imported
    global FPDF
    if FPDF is None:
        try:
            from fpdf2 import FPDF as FPDF2
            FPDF = FPDF2
            print("✅ Runtime import: Using fpdf2 for comprehensive PDF generation")
        except ImportError as e:
            print(f"❌ Runtime fpdf2 import failed: {e}")
            try:
                from fpdf import FPDF as FPDF1
                FPDF = FPDF1
                print("✅ Runtime import: Using fpdf (fallback) for comprehensive PDF generation")
            except ImportError as e2:
                print(f"❌ Runtime fpdf import also failed: {e2}")
                print("   Please ensure fpdf2 is installed: pip install fpdf2")
                import traceback
                traceback.print_exc()
                return b""
    
    if FPDF is None:
        print("❌ FPDF not available - neither fpdf2 nor fpdf could be imported")
        print("   Please ensure fpdf2 is installed: pip install fpdf2")
        import traceback
        traceback.print_exc()
        return b""
    
    try:
        # Get session from database
        try:
            session = InterviewSession.objects.get(session_key=session_key)
        except InterviewSession.DoesNotExist:
            print(f"❌ Session not found: {session_key}")
            return b""
        
        # Get AI chatbot session for Q&A transcript - try multiple lookup methods
        ai_session = None
        
        # Try 1: Look up by Django session ID
        from .ai_chatbot import chatbot_manager
        ai_session = chatbot_manager.sessions.get(str(session.id))
        
        if not ai_session:
            # Try 2: Look up in complete_ai_bot by session ID
            from .complete_ai_bot import sessions as complete_sessions
            ai_session = complete_sessions.get(str(session.id))
        
        if not ai_session:
            # Try 3: Search all sessions in complete_ai_bot for matching candidate
            from .complete_ai_bot import sessions as complete_sessions
            for sid, sess in complete_sessions.items():
                if sess.candidate_name == session.candidate_name:
                    ai_session = sess
                    print(f"✅ Found AI session by candidate name match: {sid}")
                    break
        
        if not ai_session:
            print(f"⚠️ No AI conversation history found for session {session.id}")
        
        # Get coding submissions
        coding_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
        
        # Create PDF with proper margins to prevent content overflow
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)  # Increased bottom margin
        pdf.add_page()
        # Set margins: left, top, right (in mm)
        pdf.set_left_margin(20)  # Increased from 15 to 20mm
        pdf.set_right_margin(20)  # Increased from 15 to 20mm
        pdf.set_top_margin(20)  # Set top margin
        pdf.set_auto_page_break(auto=True, margin=20)  # Ensure bottom margin
        
        # Calculate usable width (page width - left margin - right margin)
        # Standard A4 page width is 210mm
        usable_width = 210 - 20 - 20  # 170mm usable width
        
        # === HEADER ===
        pdf.set_font("Arial", "B", 18)
        pdf.cell(usable_width, 12, _sanitize_for_pdf("AI Interview Report"), ln=True, align='C')
        pdf.ln(5)
        
        # === CANDIDATE INFO ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(usable_width, 8, _sanitize_for_pdf("Candidate Information"), ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Name: {session.candidate_name}"), ln=True)
        pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Email: {session.candidate_email or 'N/A'}"), ln=True)
        pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Date: {session.created_at.strftime('%Y-%m-%d %H:%M')}"), ln=True)
        pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Session ID: {session.id}"), ln=True)
        pdf.ln(8)
        
        # === TECHNICAL Q&A SECTION ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(usable_width, 8, _sanitize_for_pdf("Technical Q&A Transcript"), ln=True)
        pdf.ln(3)
        
        # Use database InterviewQuestion records (same as serializer) for accurate Q&A pairing
        from .models import InterviewQuestion
        from django.db.models import Max
        
        # Get all questions ordered by conversation_sequence and order (same logic as serializer)
        questions = InterviewQuestion.objects.filter(
            session=session
        ).order_by(
            'conversation_sequence',
            'order',
            'id'
        )
        
        # Group questions by order to pair AI questions with Interviewee answers
        questions_by_order = {}
        for q in questions:
            order_key = q.order
            if order_key not in questions_by_order:
                questions_by_order[order_key] = {'ai': None, 'interviewee': None}
            
            # Check if this is an AI question or Interviewee answer
            if q.role == 'AI' and q.question_text:
                questions_by_order[order_key]['ai'] = q
            elif q.role == 'INTERVIEWEE' and (q.transcribed_answer or q.question_level == 'INTERVIEWEE_RESPONSE'):
                if not questions_by_order[order_key]['interviewee']:
                    questions_by_order[order_key]['interviewee'] = q
                elif q.transcribed_answer and not questions_by_order[order_key]['interviewee'].transcribed_answer:
                    # Prefer record with transcribed_answer
                    questions_by_order[order_key]['interviewee'] = q
            elif not q.role and q.question_text:
                # Old format: question_text exists, treat as AI question
                questions_by_order[order_key]['ai'] = q
        
        # Sort by order and display Q&A pairs
        sorted_orders = sorted(questions_by_order.keys())
        has_qa = False
        
        for order_key in sorted_orders:
            q_pair = questions_by_order[order_key]
            ai_q = q_pair['ai']
            interviewee_a = q_pair['interviewee']
            
            # Skip if no AI question
            if not ai_q:
                continue
            
            # Skip CODING questions (handled separately)
            if ai_q.question_type == 'CODING':
                continue
            
            has_qa = True
            
            # Question text
            question_text = ai_q.question_text or ''
            if question_text.strip().startswith('Q:'):
                question_text = question_text.replace('Q:', '').strip()
            
            # Answer text - use same logic as serializer
            answer_text = 'No answer provided'
            if interviewee_a:
                answer_text = interviewee_a.transcribed_answer or ''
                if answer_text.strip().startswith('A:'):
                    answer_text = answer_text.replace('A:', '').strip()
            
            # If no separate interviewee record, try transcribed_answer from AI question itself
            if not answer_text or answer_text == 'No answer provided':
                if ai_q.transcribed_answer:
                    answer_text = ai_q.transcribed_answer
                    if answer_text.strip().startswith('A:'):
                        answer_text = answer_text.replace('A:', '').strip()
            
            # Format answer
            if not answer_text or answer_text.strip() == '' or answer_text.lower() == 'none':
                answer_text = 'No answer provided'
            
            # Display Question
            pdf.set_font("Arial", "B", 11)
            pdf.cell(usable_width, 6, _sanitize_for_pdf("Interviewer:"), ln=True)
            
            pdf.set_font("Arial", size=10)
            # Wrap text properly to fit within page width
            wrapped_question = _wrap_text_for_pdf(question_text, max_width=65)
            safe_question = _sanitize_for_pdf(wrapped_question)
            try:
                pdf.multi_cell(usable_width, 5, safe_question, align='L')
            except Exception as e:
                # Fallback: truncate if still too long
                truncated = safe_question[:300] + "..." if len(safe_question) > 300 else safe_question
                pdf.multi_cell(usable_width, 5, truncated, align='L')
            pdf.ln(2)
            
            # Display Answer
            pdf.set_font("Arial", "B", 11)
            pdf.cell(usable_width, 6, _sanitize_for_pdf("Candidate:"), ln=True)
            
            pdf.set_font("Arial", size=10)
            # Wrap text properly to fit within page width
            wrapped_answer = _wrap_text_for_pdf(answer_text, max_width=65)
            safe_answer = _sanitize_for_pdf(wrapped_answer)
            try:
                pdf.multi_cell(usable_width, 5, safe_answer, align='L')
            except Exception as e:
                # Fallback: truncate if still too long
                truncated = safe_answer[:300] + "..." if len(safe_answer) > 300 else safe_answer
                pdf.multi_cell(usable_width, 5, truncated, align='L')
            pdf.ln(3)
        
        if not has_qa:
            pdf.set_font("Arial", "I", 11)
            pdf.cell(usable_width, 6, _sanitize_for_pdf("No Q&A transcript available"), ln=True)
        
        pdf.ln(5)
        
        # === CODING ROUND SECTION ===
        if coding_submissions.exists():
            pdf.add_page()  # New page for coding
            # Reset margins on new page
            pdf.set_left_margin(20)
            pdf.set_right_margin(20)
            pdf.set_top_margin(20)
            usable_width = 210 - 20 - 20  # Recalculate for new page
            
            pdf.set_font("Arial", "B", 14)
            pdf.cell(usable_width, 8, _sanitize_for_pdf("Coding Challenge Results"), ln=True)
            pdf.ln(3)
            
            for idx, submission in enumerate(coding_submissions, 1):
                # Get question
                from .models import InterviewQuestion
                try:
                    question = InterviewQuestion.objects.get(id=submission.question_id)
                    question_text = question.question_text
                except:
                    question_text = "Coding Challenge"
                
                # Challenge header
                pdf.set_font("Arial", "B", 12)
                pdf.cell(usable_width, 7, _sanitize_for_pdf(f"Challenge {idx}: {question_text[:60]}"), ln=True)
                pdf.ln(2)
                
                # Language and status
                pdf.set_font("Arial", size=11)
                pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Language: {submission.language}"), ln=True)
                status_text = "All Tests Passed" if submission.passed_all_tests else "Some Tests Failed"
                pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Status: {status_text}"), ln=True)
                pdf.ln(2)
                
                # Gemini evaluation if available
                if submission.gemini_evaluation:
                    gemini_score = submission.gemini_evaluation.get('score', 'N/A')
                    passed_tests = submission.gemini_evaluation.get('passed_tests', 0)
                    total_tests = submission.gemini_evaluation.get('total_tests', 0)
                    
                    pdf.set_font("Arial", "B", 11)
                    pdf.cell(usable_width, 6, _sanitize_for_pdf(f"AI Score: {gemini_score}/100"), ln=True)
                    pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Tests Passed: {passed_tests}/{total_tests}"), ln=True)
                    pdf.ln(2)
                
                # Submitted code
                pdf.set_font("Arial", "B", 11)
                pdf.cell(usable_width, 6, _sanitize_for_pdf("Submitted Code:"), ln=True)
                pdf.set_font("Courier", size=8)  # Smaller font for code
                code_lines = submission.submitted_code.split('\n')[:30]  # Limit to 30 lines
                for line in code_lines:
                    # Wrap long code lines to fit within page
                    wrapped_line = _wrap_text_for_pdf(line, max_width=75)
                    safe_line = _sanitize_for_pdf(wrapped_line)
                    try:
                        pdf.multi_cell(usable_width, 4, safe_line, align='L')
                    except Exception as e:
                        # Skip lines that are too long to render
                        pdf.set_font("Arial", "I", 8)
                        pdf.cell(usable_width, 4, _sanitize_for_pdf("... (line too long to display)"), ln=True)
                        pdf.set_font("Courier", size=8)
                
                if len(submission.submitted_code.split('\n')) > 30:
                    pdf.set_font("Arial", "I", 9)
                    pdf.cell(usable_width, 5, _sanitize_for_pdf("... (code truncated)"), ln=True)
                
                pdf.ln(3)
                
                # Test results / Output log
                if submission.output_log:
                    pdf.set_font("Arial", "B", 11)
                    pdf.cell(usable_width, 6, _sanitize_for_pdf("Test Results:"), ln=True)
                    pdf.set_font("Arial", size=9)
                    log_lines = submission.output_log.split('\n')[:20]  # Limit output
                    for line in log_lines:
                        # Wrap long lines to fit within page
                        wrapped_line = _wrap_text_for_pdf(line, max_width=70)
                        safe_line = _sanitize_for_pdf(wrapped_line)
                        try:
                            pdf.multi_cell(usable_width, 5, safe_line, align='L')
                        except Exception as e:
                            # Skip lines that cause rendering errors
                            pdf.cell(usable_width, 5, _sanitize_for_pdf("... (line skipped)"), ln=True)
                
                pdf.ln(5)
        
        # === GEMINI AI ANALYSIS ===
        pdf.add_page()
        # Reset margins on new page
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)
        pdf.set_top_margin(20)
        usable_width = 210 - 20 - 20  # Recalculate for new page
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(usable_width, 8, _sanitize_for_pdf("AI Analysis & Evaluation"), ln=True)
        pdf.ln(3)
        
        # Generate Gemini analysis for technical Q&A
        # Use database Q&A data (same as PDF generation above)
        if has_qa:
            try:
                import google.generativeai as genai
                from django.conf import settings
                api_key = getattr(settings, 'GEMINI_API_KEY', '')
                if api_key:
                    genai.configure(api_key=api_key)
                else:
                    raise ValueError("GEMINI_API_KEY not set in environment")
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                # Build conversation context from database Q&A pairs
                conversation_lines = []
                for order_key in sorted_orders:
                    q_pair = questions_by_order[order_key]
                    ai_q = q_pair['ai']
                    interviewee_a = q_pair['interviewee']
                    
                    if not ai_q or ai_q.question_type == 'CODING':
                        continue
                    
                    question_text = ai_q.question_text or ''
                    if question_text.strip().startswith('Q:'):
                        question_text = question_text.replace('Q:', '').strip()
                    
                    answer_text = 'No answer provided'
                    if interviewee_a:
                        answer_text = interviewee_a.transcribed_answer or ''
                        if answer_text.strip().startswith('A:'):
                            answer_text = answer_text.replace('A:', '').strip()
                    elif ai_q.transcribed_answer:
                        answer_text = ai_q.transcribed_answer
                        if answer_text.strip().startswith('A:'):
                            answer_text = answer_text.replace('A:', '').strip()
                    
                    if not answer_text or answer_text.strip() == '':
                        answer_text = 'No answer provided'
                    
                    conversation_lines.append(f"INTERVIEWER: {question_text}")
                    conversation_lines.append(f"CANDIDATE: {answer_text}")
                
                conversation_text = "\n".join(conversation_lines)
                
                technical_prompt = f"""
                Analyze this technical interview transcript and provide a comprehensive evaluation.
                
                Job Description: {session.job_description[:500] if session.job_description else 'AI/ML Intern'}
                Candidate: {session.candidate_name}
                
                Interview Transcript:
                {conversation_text[:3000]}
                
                Provide a structured evaluation report with the following format:
                
                OVERALL ASSESSMENT:
                • Technical Competency Score: [0-100]
                • Recommendation: [Strong/Moderate/Weak candidate]
                
                KEY STRENGTHS:
                1. [First strength with brief explanation]
                2. [Second strength with brief explanation]
                3. [Third strength with brief explanation]
                
                AREAS FOR IMPROVEMENT:
                1. [First area with specific feedback]
                2. [Second area with specific feedback]
                3. [Third area with specific feedback]
                
                TECHNICAL KNOWLEDGE ASSESSMENT:
                • [Assessment point 1]
                • [Assessment point 2]
                • [Assessment point 3]
                
                COMMUNICATION SKILLS:
                • [Communication evaluation point 1]
                • [Communication evaluation point 2]
                
                Use this exact format with numbered lists (1., 2., 3.) and bullet points (•). Keep each point concise and professional.
                """
                
                technical_response = model.generate_content(technical_prompt)
                technical_analysis = technical_response.text if technical_response.text else "Analysis unavailable"
                
                pdf.set_font("Arial", "B", 12)
                pdf.cell(usable_width, 7, _sanitize_for_pdf("Technical Interview Analysis"), ln=True)
                pdf.ln(3)
                
                # Format analysis with bullets, bold headings, and numbered lists
                formatted_lines = _format_analysis_text(technical_analysis)
                
                for item in formatted_lines:
                    if item['type'] == 'bold':
                        # Bold heading
                        pdf.set_font("Arial", "B", 11)
                        text = _wrap_text_for_pdf(item['text'], max_width=65)
                        safe_text = _sanitize_for_pdf(text)
                        pdf.multi_cell(usable_width, 6, safe_text, align='L')
                        pdf.ln(1)
                    elif item['type'] == 'number':
                        # Numbered list item
                        pdf.set_font("Arial", size=10)
                        number = item.get('number', '')
                        text = _wrap_text_for_pdf(item['text'], max_width=60)
                        safe_text = _sanitize_for_pdf(f"{number} {text}")
                        pdf.multi_cell(usable_width, 5, safe_text, align='L')
                        pdf.ln(1)
                    elif item['type'] == 'bullet':
                        # Bullet point
                        pdf.set_font("Arial", size=10)
                        indent = "  " * item.get('level', 0)
                        bullet = "• " if item.get('level', 0) == 0 else "  ◦ "
                        text = _wrap_text_for_pdf(item['text'], max_width=60)
                        safe_text = _sanitize_for_pdf(f"{indent}{bullet}{text}")
                        pdf.multi_cell(usable_width, 5, safe_text, align='L')
                        pdf.ln(1)
                    else:
                        # Normal text
                        pdf.set_font("Arial", size=10)
                        text = _wrap_text_for_pdf(item['text'], max_width=65)
                        safe_text = _sanitize_for_pdf(text)
                        pdf.multi_cell(usable_width, 5, safe_text, align='L')
                        pdf.ln(1)
                
                pdf.ln(3)
            except Exception as e:
                print(f"⚠️ Error generating technical analysis: {e}")
                pdf.set_font("Arial", "I", 11)
                pdf.cell(usable_width, 6, _sanitize_for_pdf("Technical analysis unavailable"), ln=True)
        
        # Generate Gemini analysis for coding round
        if coding_submissions.exists():
            try:
                import google.generativeai as genai
                from django.conf import settings
                api_key = getattr(settings, 'GEMINI_API_KEY', '')
                if api_key:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                else:
                    raise ValueError("GEMINI_API_KEY not set in environment")
                
                coding_analysis_text = []
                for submission in coding_submissions:
                    coding_analysis_text.append(f"""
                    Language: {submission.language}
                    Code: {submission.submitted_code[:1000]}
                    Tests Passed: {'Yes' if submission.passed_all_tests else 'No'}
                    Output: {submission.output_log[:500] if submission.output_log else 'N/A'}
                    """)
                
                coding_prompt = f"""
                Analyze this coding challenge submission and provide evaluation.
                
                Submissions:
                {''.join(coding_analysis_text)}
                
                Provide a structured evaluation report with the following format:
                
                OVERALL ASSESSMENT:
                • Code Quality Score: [0-100]
                • Overall Coding Competency: [Excellent/Good/Moderate/Needs Improvement]
                
                CODE QUALITY ANALYSIS:
                1. [First quality aspect with explanation]
                2. [Second quality aspect with explanation]
                3. [Third quality aspect with explanation]
                
                PROBLEM-SOLVING APPROACH:
                • [Approach evaluation point 1]
                • [Approach evaluation point 2]
                • [Approach evaluation point 3]
                
                CODE CORRECTNESS & EFFICIENCY:
                1. [Correctness point with details]
                2. [Efficiency point with details]
                
                BEST PRACTICES ADHERENCE:
                • [Practice 1 assessment]
                • [Practice 2 assessment]
                • [Practice 3 assessment]
                
                SUGGESTIONS FOR IMPROVEMENT:
                1. [First suggestion]
                2. [Second suggestion]
                3. [Third suggestion]
                
                Use this exact format with numbered lists (1., 2., 3.) and bullet points (•). Keep each point concise and professional.
                """
                
                coding_response = model.generate_content(coding_prompt)
                coding_analysis = coding_response.text if coding_response.text else "Analysis unavailable"
                
                pdf.set_font("Arial", "B", 12)
                pdf.cell(usable_width, 7, _sanitize_for_pdf("Coding Challenge Analysis"), ln=True)
                pdf.ln(3)
                
                # Format analysis with bullets, bold headings, and numbered lists
                formatted_lines = _format_analysis_text(coding_analysis)
                
                for item in formatted_lines:
                    if item['type'] == 'bold':
                        # Bold heading
                        pdf.set_font("Arial", "B", 11)
                        text = _wrap_text_for_pdf(item['text'], max_width=65)
                        safe_text = _sanitize_for_pdf(text)
                        pdf.multi_cell(usable_width, 6, safe_text, align='L')
                        pdf.ln(1)
                    elif item['type'] == 'number':
                        # Numbered list item
                        pdf.set_font("Arial", size=10)
                        number = item.get('number', '')
                        text = _wrap_text_for_pdf(item['text'], max_width=60)
                        safe_text = _sanitize_for_pdf(f"{number} {text}")
                        pdf.multi_cell(usable_width, 5, safe_text, align='L')
                        pdf.ln(1)
                    elif item['type'] == 'bullet':
                        # Bullet point
                        pdf.set_font("Arial", size=10)
                        indent = "  " * item.get('level', 0)
                        bullet = "• " if item.get('level', 0) == 0 else "  ◦ "
                        text = _wrap_text_for_pdf(item['text'], max_width=60)
                        safe_text = _sanitize_for_pdf(f"{indent}{bullet}{text}")
                        pdf.multi_cell(usable_width, 5, safe_text, align='L')
                        pdf.ln(1)
                    else:
                        # Normal text
                        pdf.set_font("Arial", size=10)
                        text = _wrap_text_for_pdf(item['text'], max_width=65)
                        safe_text = _sanitize_for_pdf(text)
                        pdf.multi_cell(usable_width, 5, safe_text, align='L')
                        pdf.ln(1)
            except Exception as e:
                print(f"⚠️ Error generating coding analysis: {e}")
                pdf.set_font("Arial", "I", 11)
                pdf.cell(usable_width, 6, _sanitize_for_pdf("Coding analysis unavailable"), ln=True)
        
        # === OVERALL EVALUATION ===
        if session.overall_performance_feedback or session.overall_performance_score:
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(usable_width, 7, _sanitize_for_pdf("Overall Performance Summary"), ln=True)
            pdf.ln(2)
            
            if session.overall_performance_score:
                pdf.set_font("Arial", "B", 11)
                pdf.cell(usable_width, 6, _sanitize_for_pdf(f"Overall Score: {session.overall_performance_score:.1f}/100"), ln=True)
                pdf.ln(2)
            
            if session.overall_performance_feedback:
                pdf.set_font("Arial", size=10)
                feedback_text = _sanitize_for_pdf(_wrap_long_words(session.overall_performance_feedback))
                try:
                    pdf.multi_cell(usable_width, 6, feedback_text, align='L')
                except:
                    pdf.cell(usable_width, 6, _sanitize_for_pdf(feedback_text[:300] + "..."), ln=True)
        
        # Generate PDF bytes
        data = pdf.output(dest='S')
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        return str(data).encode('latin1', 'replace')
        
    except Exception as e:
        print(f"❌ Error generating comprehensive PDF: {e}")
        import traceback
        traceback.print_exc()
        return b""


def ai_comprehensive_pdf_django(session_key: str) -> bytes:
    """
    Generate comprehensive PDF for a session (wrapper for views.py)
    """
    return generate_comprehensive_pdf(session_key)

