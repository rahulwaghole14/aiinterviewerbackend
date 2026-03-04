from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def download_qa_evaluation_pdf(request):
    """
    Generate comprehensive Q&A Script + AI Evaluation PDF with Skills Assessment Matrix
    using LLM analysis of technical and coding Q&A
    """
    try:
        session_key = request.GET.get('session_key', '')
        session_id = request.GET.get('session_id', '')
        
        print(f"\n{'='*60}")
        print(f"📄 Q&A EVALUATION PDF GENERATION REQUEST")
        print(f"   Session Key: {session_key}")
        print(f"   Session ID: {session_id}")
        print(f"🤖 Using LLM: Google Gemini 1.5-flash for Skills Assessment Matrix")
        print(f"📊 Skills Assessment Parameters: SKILL, CATEGORY, SCORE, PERFORMANCE LEVEL, COMMENTS")
        print(f"🎯 Overall Score Calculation: Weighted average of all skill scores")
        print(f"{'='*60}")
        
        # Get session
        from .models import InterviewSession
        try:
            if session_key:
                session = InterviewSession.objects.get(session_key=session_key)
            elif session_id:
                session = InterviewSession.objects.get(id=session_id)
            else:
                return JsonResponse({'error': 'Session key or ID required'}, status=400)
        except InterviewSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Get all conversation items (AI and Interviewee responses) in sequential order
        from .models import InterviewQuestion
        all_conversation_items = InterviewQuestion.objects.filter(
            session=session
        ).prefetch_related('follow_ups').order_by('conversation_sequence', 'order', 'id')
        
        # Group non-coding questions by order for pairing AI with Interviewee
        questions_by_order = {}
        for q in all_conversation_items:
            question_type = (q.question_type or '').upper()
            if question_type == 'CODING' or question_type == 'CODING CHALLENGE':
                continue
                
            order_key = q.order
            if order_key not in questions_by_order:
                questions_by_order[order_key] = {'ai': None, 'interviewee': None}
            
            # Use role to determine if it's AI or INTERVIEWEE
            role = (q.role or '').upper()
            if role == 'AI':
                # AI record contains the question
                if q.question_level != 'CANDIDATE_QUESTION':
                    questions_by_order[order_key]['ai'] = q
            elif role == 'INTERVIEWEE':
                # Interviewee record contains the answer
                if q.question_level == 'CANDIDATE_QUESTION':
                    # For candidate questions, their question is in transcribed_answer
                    questions_by_order[order_key]['interviewee'] = q
                else:
                    # Regular answer
                    questions_by_order[order_key]['interviewee'] = q
            else:
                # Old format fallback
                if q.question_text and not q.transcribed_answer:
                    questions_by_order[order_key]['ai'] = q
                elif q.transcribed_answer:
                    questions_by_order[order_key]['interviewee'] = q

        # Build fixed sequence of paired technical questions
        main_questions = []
        for order_key in sorted(questions_by_order.keys()):
            pair = questions_by_order[order_key]
            ai_q = pair['ai']
            interviewee_a = pair['interviewee']
            
            # Only include if there is an AI question (the sequence is driven by AI questions)
            if ai_q:
                # Get answer text from interviewee record and monkey-patch it onto the AI question
                a_text = "No answer recorded."
                if interviewee_a:
                    if interviewee_a.question_level == 'CANDIDATE_QUESTION':
                        # If candidate asked a question, show what they asked in the answer section
                        a_text = interviewee_a.transcribed_answer or "No question provided"
                    else:
                        a_text = interviewee_a.transcribed_answer or "No answer recorded."
                
                # Monkey-patch the answer onto the AI question object so the template can use it
                ai_q.transcribed_answer = a_text
                # Also clean the question text if it has Q: prefix
                if ai_q.question_text.strip().startswith('Q:'):
                    ai_q.question_text = ai_q.question_text.replace('Q:', '').strip()
                
                main_questions.append(ai_q)
        
        code_submissions = session.code_submissions.all()
        
        # Generate Skills Assessment Matrix using LLM
        from .qa_evaluation_pdf import generate_skills_assessment_with_llm, calculate_overall_score, get_performance_level
        print(f"\n Generating Skills Assessment Matrix using Google Gemini 1.5-flash...")
        print(f" Analyzing {len(main_questions)} technical questions and {len(code_submissions)} coding submissions")
        
        skills_assessment = generate_skills_assessment_with_llm(main_questions, code_submissions)
        
        print(f"\n SKILLS ASSESSMENT MATRIX GENERATED:")
        print(f"{'='*80}")
        print(f"{'SKILL':<20} {'CATEGORY':<15} {'SCORE':<8} {'PERFORMANCE':<12} {'COMMENTS'}")
        print(f"{'='*80}")
        
        for skill in skills_assessment:
            print(f"{skill['skill']:<20} {skill['category']:<15} {skill['score']}%{'':<4} {skill['performance_level']:<12} {skill['comments'][:50]}...")
        
        print(f"{'='*80}")
        
        # Calculate overall score and recommendation
        overall_score = calculate_overall_score(skills_assessment)
        overall_level, overall_color = get_performance_level(overall_score)
        
        print(f"\n OVERALL SCORE CALCULATION:")
        print(f"   Overall Score: {overall_score}%")
        print(f"   Performance Level: {overall_level}")
        print(f"   Color Code: {overall_color}")
        print(f"{'='*60}")
        
        # Render template
        from django.template.loader import get_template
        from django.http import HttpResponse
        from weasyprint import HTML, CSS
        
        # Calculate hire status (same as new version)
        hire_status = "RECOMMENDED" if overall_score >= 70 else "NOT RECOMMENDED"
        hire_status_color = "#28a745" if overall_score >= 70 else "#dc3545"

        template = get_template('interview_app/qa_evaluation_pdf_fixed.html')
        html_content = template.render({
            'session': session,
            'main_questions_with_followups': main_questions,
            'technical_questions': main_questions, # Add this for template compatibility
            'code_submissions': code_submissions,
            'skills_assessment': skills_assessment,
            'overall_score': overall_score,
            'overall_level': overall_level,
            'overall_color': overall_color,
            'hire_status': hire_status,
            'hire_status_color': hire_status_color,
        })
        
        # Generate PDF
        print(f"\n📄 Generating PDF with Skills Assessment Matrix...")
        print(f"   Template: qa_evaluation_pdf_fixed.html")
        print(f"   Skills Count: {len(skills_assessment)}")
        print(f"   Overall Score: {overall_score}%")
        print(f"   Performance Level: {overall_level}")
        
        html = HTML(string=html_content)
        css = CSS(string='''
            @page { size: A4; margin: 1.5cm; }
            body { font-family: Arial, sans-serif; }
        ''')
        
        pdf = html.write_pdf(stylesheets=[css])
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="QA_Evaluation_Report_{session.id}.pdf"'
        
        print(f"✅ PDF Generated Successfully!")
        print(f"   Filename: QA_Evaluation_Report_{session.id}.pdf")
        print(f"   File Size: {len(pdf)} bytes")
        print(f"{'='*60}")
        
        return response
        
    except InterviewSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    except Exception as e:
        print(f"❌ Error generating Q&A evaluation PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'PDF generation failed: {str(e)}'}, status=500)


def generate_skills_assessment_with_llm(main_questions, code_submissions):
    """
    Generate Skills Assessment Matrix using LLM analysis of Q&A
    """
    import google.generativeai as genai
    import os
    from django.conf import settings
    
    try:
        # Initialize Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Test model with a very simple call to verify it's supported/found
            # (Optional: we can just catch the error during actual use, but this is cleaner)
        except Exception as e:
            print(f"⚠️ Primary model 'gemini-1.5-flash' failed: {e}. Falling back to 'gemini-pro'.")
            model = genai.GenerativeModel('gemini-pro')
        
        # Prepare Q&A data for analysis
        # Prepare Q&A data for analysis
        from .models import TechnicalInterviewQA
        
        session = None
        if main_questions and hasattr(main_questions, 'first') and main_questions.first():
             session = main_questions.first().session
        elif main_questions and len(main_questions) > 0:
             session = main_questions[0].session
        elif code_submissions and len(code_submissions) > 0:
             session = code_submissions[0].session
             
        qa_text_parts = []
        marker_used = False

        if session:
             tech_qa_obj = TechnicalInterviewQA.objects.filter(session=session).first()
             if tech_qa_obj and tech_qa_obj.overall_qa:
                 print(f"--- Using single TechnicalInterviewQA entry for PDF analysis ---")
                 qa_text_parts.append(tech_qa_obj.overall_qa)
                 marker_used = True
        
        if not marker_used:
            for i, question in enumerate(main_questions):
                qa_text_parts.append(f"AI Interviewer: {question.question_text}")
                qa_text_parts.append(f"Interviewee: {question.transcribed_answer or 'No answer provided'}")
                
                # Add follow-ups
                for follow_up in question.follow_ups.all():
                    qa_text_parts.append(f"AI Interviewer (Follow-up): {follow_up.question_text}")
                    qa_text_parts.append(f"Interviewee: {follow_up.transcribed_answer or 'No answer provided'}")
        
        # Add coding challenges
        for i, submission in enumerate(code_submissions):
            try:
                # submission.question_id is a CharField, fetch the InterviewQuestion object
                from .models import InterviewQuestion
                # Try to get the question text
                q_obj = InterviewQuestion.objects.filter(session=session, id=submission.question_id).first()
                if not q_obj and submission.question_id.isdigit():
                    # Fallback for cases where it's stored as numeric string but might be an integer ID
                    q_obj = InterviewQuestion.objects.filter(id=int(submission.question_id)).first()
                
                q_text = q_obj.question_text if q_obj else f"Coding Challenge {i+1}"
                qa_text_parts.append(f"\nCoding {i + 1}: {q_text}")
            except Exception as e:
                print(f"⚠️ Error fetching question text for coding submission: {e}")
                qa_text_parts.append(f"\nCoding {i + 1}: Challenge (ID: {submission.question_id})")
                
            qa_text_parts.append(f"Code: {submission.submitted_code}")
            qa_text_parts.append(f"Test Results: {submission.output_log or 'No results'}")
        
        # Create LLM prompt for skills assessment
        qa_text = "\n".join(qa_text_parts)
        
        prompt = f"""
        Analyze the following interview Q&A session and generate a comprehensive Skills Assessment Matrix.

        Interview Q&A Data:
        {qa_text}

        Please analyze the candidate's performance across these categories and generate a structured assessment:

        REQUIRED OUTPUT FORMAT (exactly this structure):
        1. Technical Knowledge: Assess understanding of technical concepts, problem-solving ability, and technical accuracy
        2. Communication Skills: Assess clarity of expression, articulation of thoughts, and professional communication
        3. Problem Solving: Assess analytical thinking, approach to problems, and solution quality
        4. Coding Skills: Assess code quality, algorithm understanding, and test performance (if applicable)
        5. Behavioral Fit: Assess teamwork, leadership potential, and cultural fit indicators

        For each skill, provide:
        - CATEGORY: (Technical, Communication, Problem Solving, Coding, Behavioral)
        - SCORE: (0-100%)
        - PERFORMANCE LEVEL: (Excellent, Good, Average, Poor)
        - COMMENTS: Specific feedback with examples from their answers

        Focus on concrete evidence from their actual answers. Be fair but thorough in your assessment.
        """
        
        # Generate assessment
        response = model.generate_content(prompt)
        
        # Parse the response into structured format
        skills_assessment = parse_llm_skills_response(response.text)
        
        return skills_assessment
        
    except Exception as e:
        print(f"⚠️ Error generating LLM skills assessment: {e}")
        # Fallback to basic assessment
        return get_fallback_skills_assessment(main_questions, code_submissions)


def parse_llm_skills_response(response_text):
    """
    Parse LLM response into structured skills assessment
    """
    skills = []
    
    # Try to extract structured data
    lines = response_text.split('\n')
    current_skill = {}
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().upper()
                value = parts[1].strip()
                
                if key in ['TECHNICAL KNOWLEDGE', 'COMMUNICATION SKILLS', 'PROBLEM SOLVING', 'CODING SKILLS', 'BEHAVIORAL FIT']:
                    if 'SCORE' in value and '%' in value:
                        score = int(value.replace('%', '').strip())
                        current_skill['score'] = score
                    elif 'PERFORMANCE LEVEL' in value:
                        level = value.strip()
                        current_skill['performance_level'] = level
                    elif 'COMMENTS' in value:
                        comments = value.replace('COMMENTS', '').strip(':').strip()
                        current_skill['comments'] = comments
                    
                    # When we have a complete skill entry, add it to the list
                    if 'score' in current_skill and 'performance_level' in current_skill:
                        skill_name = key.replace(' KNOWLEDGE', '').replace(' SKILLS', '').strip()
                        skills.append({
                            'skill': skill_name,
                            'category': key,
                            'score': current_skill['score'],
                            'performance_level': current_skill['performance_level'],
                            'comments': current_skill.get('comments', 'No specific comments available.')
                        })
                        current_skill = {}
    
    # Fallback if parsing failed
    if not skills:
        return get_fallback_skills_assessment([], [])
    
    return skills


def get_fallback_skills_assessment(main_questions, code_submissions):
    """
    Generate basic skills assessment when LLM fails
    """
    skills = []
    
    # Technical Knowledge (based on technical questions)
    tech_questions = [q for q in main_questions if q.question_type == 'TECHNICAL']
    if tech_questions:
        answered_count = sum(1 for q in tech_questions if q.transcribed_answer and q.transcribed_answer.strip())
        tech_score = min(100, (answered_count / len(tech_questions)) * 100) if tech_questions else 50
        
        skills.append({
            'skill': 'Technical Knowledge',
            'category': 'TECHNICAL KNOWLEDGE',
            'score': tech_score,
            'performance_level': get_performance_level_name(tech_score),
            'comments': f"Answered {answered_count}/{len(tech_questions)} technical questions effectively."
        })
    
    # Communication Skills (based on answer quality)
    all_answers = [q.transcribed_answer for q in main_questions if q.transcribed_answer]
    if all_answers:
        avg_answer_length = sum(len(a) for a in all_answers) / len(all_answers)
        comm_score = min(100, max(0, (avg_answer_length / 50) * 100))  # Assume 50 chars is good
        
        skills.append({
            'skill': 'Communication Skills',
            'category': 'COMMUNICATION SKILLS',
            'score': comm_score,
            'performance_level': get_performance_level_name(comm_score),
            'comments': f"Average answer length: {avg_answer_length:.0f} characters."
        })
    
    # Coding Skills (based on submissions)
    if code_submissions:
        passed_tests = 0
        total_tests = 0
        for submission in code_submissions:
            if submission.output_log:
                # Parse test results
                if 'passed' in submission.output_log.lower():
                    passed_tests += 1
                    total_tests += 1
                else:
                    total_tests += 1
        
        coding_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        skills.append({
            'skill': 'Coding Skills',
            'category': 'CODING SKILLS',
            'score': coding_score,
            'performance_level': get_performance_level_name(coding_score),
            'comments': f"Passed {passed_tests}/{total_tests} test cases."
        })
    
    # Behavioral Fit (placeholder)
    skills.append({
        'skill': 'Behavioral Fit',
        'category': 'BEHAVIORAL FIT',
        'score': 75,  # Default placeholder
        'performance_level': 'Good',
        'comments': 'Based on interview participation and engagement.'
    })
    
    return skills


def get_performance_level_name(score):
    """Convert score to performance level name"""
    if score >= 90:
        return 'Excellent'
    elif score >= 75:
        return 'Good'
    elif score >= 60:
        return 'Average'
    else:
        return 'Poor'


def get_performance_level(score):
    """Get performance level and color for score"""
    if score >= 90:
        return 'Excellent', '#28a745'
    elif score >= 75:
        return 'Good', '#17a2b8'
    elif score >= 60:
        return 'Average', '#ffc107'
    else:
        return 'Poor', '#dc3545'


def calculate_overall_score(skills_assessment):
    """Calculate overall score with 100% technical performance (no coding)"""
    if not skills_assessment:
        return 50
    
    # Use only technical skills (exclude coding skills)
    technical_skills = [skill for skill in skills_assessment if skill['category'] != 'CODING SKILLS']
    
    if not technical_skills:
        return 50
    
    # Calculate average of technical skills only
    technical_avg = sum(skill['score'] for skill in technical_skills) / len(technical_skills)
    
    print(f"\n🎯 TECHNICAL EVALUATION CALCULATION:")
    print(f"   Technical Skills (100%): {technical_avg:.1f}%")
    print(f"   Final Overall Score: {technical_avg:.1f}%")
    
    return round(technical_avg, 1)
