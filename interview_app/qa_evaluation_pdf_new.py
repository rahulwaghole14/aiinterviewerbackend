from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from .models import InterviewSession, InterviewQuestion, CodeSubmission

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
        print(f"🎯 Overall Score Calculation: 100% Technical Performance Only")
        print(f"{'='*60}")
        
        # Get session
        try:
            if session_key:
                session = InterviewSession.objects.get(session_key=session_key)
            elif session_id:
                session = InterviewSession.objects.get(id=session_id)
            else:
                return JsonResponse({'error': 'Session key or ID required'}, status=400)
        except InterviewSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # 1. Get all questions ordered by order and sequence
        all_items = InterviewQuestion.objects.filter(session=session).order_by('order', 'conversation_sequence', 'id')
        
        # 2. Group and Deduplicate by order
        pairs = {} # order -> {ai: ..., interviewee: ...}
        for q in all_items:
            if (q.question_type or '').upper() in ['CODING', 'CODING CHALLENGE']: continue
            
            ord_key = q.order
            if ord_key not in pairs:
                pairs[ord_key] = {'ai': None, 'interviewee': None}
            
            role = (q.role or '').upper()
            q_level = (q.question_level or '').upper()
            
            if role == 'AI' or q_level == 'AI_RESPONSE':
                if not pairs[ord_key]['ai']: pairs[ord_key]['ai'] = q
            elif role == 'INTERVIEWEE' or q_level == 'CANDIDATE_QUESTION':
                if not pairs[ord_key]['interviewee']: pairs[ord_key]['interviewee'] = q

        # 3. Construct the technical questions list
        technical_questions = []
        for ord_key in sorted(pairs.keys()):
            pair = pairs[ord_key]
            ai_q, int_a = pair['ai'], pair['interviewee']
            
            if ai_q:
                if ai_q.question_level == 'AI_RESPONSE':
                    ai_q.question_text = f"AI Response: {ai_q.question_text}"
                
                if int_a:
                    ans_text = int_a.transcribed_answer or "No answer recorded."
                    if int_a.question_level == 'CANDIDATE_QUESTION':
                        ans_text = f"[Candidate Asked]: {ans_text}"
                    ai_q.transcribed_answer = ans_text
                else:
                    ai_q.transcribed_answer = "No answer recorded."
                
                if ai_q.question_text.startswith('Q:'): ai_q.question_text = ai_q.question_text[2:].strip()
                if (ai_q.question_type or '').upper() in ['TECHNICAL', 'BEHAVIORAL']:
                    technical_questions.append(ai_q)
            elif int_a and int_a.question_level == 'CANDIDATE_QUESTION':
                int_a.question_text = f"[Question Asked by Candidate]: {int_a.transcribed_answer}"
                int_a.transcribed_answer = "-"
                technical_questions.append(int_a)

        code_submissions = list(session.code_submissions.all())
        # Attach question text to each submission for use in template and LLM
        for submission in code_submissions:
            try:
                q_id = submission.question_id
                q_obj = InterviewQuestion.objects.filter(session=session, id=q_id).first()
                if not q_obj and q_id.isdigit():
                    q_obj = InterviewQuestion.objects.filter(id=int(q_id)).first()
                submission.question_text = q_obj.question_text if q_obj else f"Coding Challenge {q_id}"
            except Exception as e:
                print(f"⚠️ Error attaching question text to submission: {e}")
                submission.question_text = f"Coding Challenge {submission.question_id}"

        from .qa_evaluation_pdf import generate_skills_assessment_with_llm, calculate_overall_score, get_performance_level
        print(f"\n🚀 Generating Skills Assessment Matrix using Google Gemini 1.5-flash...")
        print(f"📋 Analyzing {len(technical_questions)} technical questions and {len(code_submissions)} coding submissions")
        print(f"📊 Total Questions in Session: {len(all_items)} (deduplicated: {len(technical_questions)})")
        
        skills_assessment = generate_skills_assessment_with_llm(technical_questions, code_submissions)
        
        print(f"\n📊 SKILLS ASSESSMENT MATRIX GENERATED:")
        print(f"{'='*80}")
        print(f"{'SKILL':<20} {'CATEGORY':<15} {'SCORE':<8} {'PERFORMANCE':<12} {'COMMENTS'}")
        print(f"{'='*80}")
        
        for skill in skills_assessment:
            print(f"{skill['skill']:<20} {skill['category']:<15} {skill['score']}%{'':<4} {skill['performance_level']:<12} {skill['comments'][:50]}...")
        
        print(f"{'='*80}")
        
        # Calculate overall score and recommendation
        overall_score = calculate_overall_score(skills_assessment)
        overall_level, overall_color = get_performance_level(overall_score)
        
        # Determine hire status based on coding + technical performance
        hire_status = "RECOMMENDED" if overall_score >= 70 else "NOT RECOMMENDED"
        hire_status_color = "#28a745" if overall_score >= 70 else "#dc3545"
        
        print(f"\n🎯 OVERALL SCORE CALCULATION:")
        print(f"   Overall Score: {overall_score}%")
        print(f"   Performance Level: {overall_level}")
        print(f"   Hire Status: {hire_status}")
        print(f"   Color Code: {overall_color}")
        print(f"{'='*60}")
        
        # Render template
        from django.template.loader import get_template
        from django.http import HttpResponse
        from weasyprint import HTML, CSS
        
        print(f"\n📄 Generating PDF with Skills Assessment Matrix...")
        print(f"   Template: qa_evaluation_pdf_fixed.html")
        print(f"   Skills Count: {len(skills_assessment)}")
        print(f"   Overall Score: {overall_score}%")
        print(f"   Performance Level: {overall_level}")
        
        template = get_template('interview_app/qa_evaluation_pdf_fixed.html')
        html_content = template.render({
            'session': session,
            'technical_questions': technical_questions,
            'code_submissions': code_submissions,
            'skills_assessment': skills_assessment,
            'overall_score': overall_score,
            'overall_level': overall_level,
            'overall_color': overall_color,
            'hire_status': hire_status,
            'hire_status_color': hire_status_color,
        })
        
        # Generate PDF
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
