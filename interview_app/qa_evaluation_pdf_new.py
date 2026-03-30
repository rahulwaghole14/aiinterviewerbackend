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
        
        # Get technical questions using the same method as the UI (from InterviewSerializer)
        from interviews.serializers import InterviewSerializer
        serializer = InterviewSerializer()
        
        # Get the interview object for the serializer
        from interviews.models import Interview
        interview = Interview.objects.filter(session_key=session.session_key).first()
        
        # Get questions and answers using the same logic as the UI
        qa_data = serializer.get_questions_and_answers(interview) if interview else []
        all_questions = qa_data if isinstance(qa_data, list) else qa_data.get('technical_questions', [])
        
        # Separate technical questions from coding questions
        technical_questions = [q for q in all_questions if q.get('question_type') != 'CODING']
        coding_questions = [q for q in all_questions if q.get('question_type') == 'CODING']
        
        print(f"\n📋 Retrieved {len(technical_questions)} technical questions from QAConversationPair")
        print(f"🔧 Retrieved {len(coding_questions)} coding questions")
        
        for i, qa in enumerate(technical_questions[:3]):  # Show first 3 for debugging
            print(f"   Q{i+1}: {qa.get('question_text', 'N/A')[:50]}...")
            print(f"   A{i+1}: {qa.get('answer_text', 'N/A')[:50]}...")

        # Get AI analysis data for detailed evaluation sections
        ai_analysis = {}
        section_scores_data = []
        technical_metrics = {}
        coding_metrics = {}
        try:
            from interviews.models import Interview
            from interviews.serializers import InterviewSerializer
            interview_obj = Interview.objects.filter(session_key=session.session_key).first()
            if interview_obj:
                # Use same serializer as frontend to get consistent data
                serializer = InterviewSerializer(interview_obj)
                ai_analysis = serializer.data.get('ai_result', {})
                print(f" Found AI analysis data for interview via serializer")
                print(f"   - Technical Score: {ai_analysis.get('technical_score', 'N/A')}")
                print(f"   - Coding Score: {ai_analysis.get('coding_score', 'N/A')}")
                print(f"   - Communication Score: {ai_analysis.get('communication_score', 'N/A')}")
                print(f"   - Behavioral Score: {ai_analysis.get('behavioral_score', 'N/A')}")
                
                # Calculate TECHNICAL metrics using EXACT same logic as frontend
                technical_total_questions = ai_analysis.get('technical_questions_attempted', ai_analysis.get('questions_attempted', len(technical_questions)))
                technical_correct_answers = 0
                technical_accuracy = 0
                
                # Priority 1: Use technical_questions_correct and technical_questions_attempted (most accurate)
                if ai_analysis.get('technical_questions_correct') is not None and ai_analysis.get('technical_questions_attempted') is not None:
                    technical_correct_answers = int(round(ai_analysis.get('technical_questions_correct', 0)))
                    technical_attempted = int(round(ai_analysis.get('technical_questions_attempted', 0)))
                    technical_accuracy = (technical_correct_answers / technical_attempted * 100) if technical_attempted > 0 else 0
                    print(f"   ✅ Using LLM analysis (technical_questions_*): {technical_correct_answers}/{technical_attempted} correct")
                # Priority 2: Use questions_correct and questions_attempted (backward compatibility)
                elif ai_analysis.get('questions_correct') is not None and ai_analysis.get('questions_attempted') is not None:
                    technical_correct_answers = int(round(ai_analysis.get('questions_correct', 0)))
                    technical_attempted = int(round(ai_analysis.get('questions_attempted', 0)))
                    technical_total_questions = technical_attempted
                    technical_accuracy = (technical_correct_answers / technical_attempted * 100) if technical_attempted > 0 else 0
                    print(f"   ✅ Using LLM analysis (questions_*): {technical_correct_answers}/{technical_attempted} correct")
                # Priority 3: Use AI-provided technical_accuracy_percentage
                elif ai_analysis.get('technical_accuracy_percentage') is not None and ai_analysis.get('technical_questions_attempted') is not None:
                    technical_attempted = int(round(ai_analysis.get('technical_questions_attempted', 0)))
                    technical_accuracy = ai_analysis.get('technical_accuracy_percentage', 0)
                    technical_correct_answers = int(round((technical_accuracy / 100) * technical_attempted))
                    technical_total_questions = technical_attempted
                    print(f"   ✅ Using LLM analysis (from accuracy %): {technical_correct_answers}/{technical_attempted} correct")
                # Priority 4: Use AI-provided technical_score to estimate correct answers
                elif ai_analysis.get('technical_score') is not None:
                    technical_score = ai_analysis.get('technical_score', 0)
                    technical_correct_answers = int(round((technical_score / 100) * technical_total_questions))
                    technical_accuracy = (technical_correct_answers / technical_total_questions * 100) if technical_total_questions > 0 else 0
                    print(f"   ✅ Using LLM analysis (from technical score): {technical_correct_answers}/{technical_total_questions} correct")
                # Fallback: count from technical_questions if they have is_correct flag from AI analysis
                else:
                    # Count from qa.is_correct flag if available
                    technical_with_correctness = [qa for qa in technical_questions if hasattr(qa, 'is_correct') and qa.is_correct is True]
                    technical_correct_answers = len(technical_with_correctness)
                    technical_accuracy = (technical_correct_answers / technical_total_questions * 100) if technical_total_questions > 0 else 0
                    print(f"   ⚠️ Using fallback calculation: {technical_correct_answers}/{technical_total_questions} correct")
                
                # Calculate CODING metrics using EXACT same logic as frontend
                coding_total_questions = ai_analysis.get('coding_questions_attempted', len(coding_questions))
                coding_correct_answers = 0
                coding_accuracy = 0
                
                # Priority 1: Use AI analysis results for coding questions
                if ai_analysis.get('coding_questions_correct') is not None and ai_analysis.get('coding_questions_attempted') is not None:
                    coding_correct_answers = int(round(ai_analysis.get('coding_questions_correct', 0)))
                    coding_attempted = int(round(ai_analysis.get('coding_questions_attempted', 0)))
                    coding_total_questions = coding_attempted
                    coding_accuracy = (coding_correct_answers / coding_attempted * 100) if coding_attempted > 0 else 0
                    print(f"   ✅ Using LLM analysis for coding: {coding_correct_answers}/{coding_attempted} correct")
                # Priority 2: Use AI coding score to estimate correct answers
                elif ai_analysis.get('coding_score') is not None:
                    coding_score = ai_analysis.get('coding_score', 0)
                    coding_correct_answers = int(round((coding_score / 100) * coding_total_questions))
                    coding_accuracy = (coding_correct_answers / coding_total_questions * 100) if coding_total_questions > 0 else 0
                    print(f"   ✅ Using AI coding score: {coding_correct_answers}/{coding_total_questions} correct")
                # Fallback: Use test results for coding questions
                else:
                    if coding_questions:
                        # Count passed coding submissions
                        coding_correct_answers = sum(1 for q in coding_questions 
                                                   if hasattr(q, 'code_submission') and q.code_submission and q.code_submission.passed_all_tests)
                    coding_accuracy = (coding_correct_answers / coding_total_questions * 100) if coding_total_questions > 0 else 0
                    print(f"   ⚠️ Using test results for coding: {coding_correct_answers}/{coding_total_questions} correct")
                
                # Create metrics data like frontend
                technical_metrics = {
                    'total_questions': technical_total_questions,
                    'correct_answers': technical_correct_answers,
                    'accuracy': technical_accuracy,
                    'correct_percentage': (technical_correct_answers / technical_total_questions * 100) if technical_total_questions > 0 else 0
                }
                
                coding_metrics = {
                    'total_questions': coding_total_questions,
                    'correct_answers': coding_correct_answers,
                    'accuracy': coding_accuracy,
                    'correct_percentage': (coding_correct_answers / coding_total_questions * 100) if coding_total_questions > 0 else 0
                }
                
                print(f"   - Technical Metrics: {technical_total_questions} total, {technical_correct_answers} correct, {technical_accuracy:.1f}% accuracy")
                print(f"   - Coding Metrics: {coding_total_questions} total, {coding_correct_answers} correct, {coding_accuracy:.1f}% accuracy")
                
                # Create section scores data like frontend
                section_scores_data = [
                    {
                        'name': 'Technical Skills',
                        'score': ai_analysis.get('technical_score', 0),
                        'color': '#2196F3'
                    },
                    {
                        'name': 'Communication Skills',
                        'score': ai_analysis.get('communication_score', 0),
                        'color': '#4CAF50'
                    }
                ]
                
                # Add coding skills if coding questions exist
                if coding_questions:
                    section_scores_data.append({
                        'name': 'Coding Skills',
                        'score': ai_analysis.get('coding_score', 0),
                        'color': '#FF9800'
                    })
                
                # Add behavioral assessment
                section_scores_data.append({
                    'name': 'Behavioral Assessment',
                    'score': ai_analysis.get('behavioral_score', 0),
                    'color': '#9C27B0'
                })
                
                print(f"   - Created {len(section_scores_data)} section scores")
            else:
                print(f" No interview object found for session key")
        except Exception as e:
            print(f" Error getting AI analysis: {e}")
            import traceback
            traceback.print_exc()
            ai_analysis = {}
            section_scores_data = []
            technical_metrics = {'total_questions': len(technical_questions), 'correct_answers': 0, 'accuracy': 0}
            coding_metrics = {'total_questions': len(coding_questions), 'correct_answers': 0, 'accuracy': 0}

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
        
        # Convert dictionary data to format expected by skills assessment functions
        # Create mock objects with the required attributes
        class MockQuestion:
            def __init__(self, data):
                self.question_type = data.get('question_type', 'TECHNICAL')
                self.question_text = data.get('question_text', '')
                self.transcribed_answer = data.get('answer_text', '')
                self.session = session
        
        mock_questions = [MockQuestion(q) for q in technical_questions]
        
        skills_assessment = generate_skills_assessment_with_llm(mock_questions, code_submissions)
        
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
        
        # Use exact same hire status and score as frontend
        # Frontend uses: ai_result.hire_recommendation and ai_result.total_score
        frontend_hire_status = ai_analysis.get('hire_recommendation', False)
        frontend_total_score = ai_analysis.get('total_score', 0)
        
        # Convert frontend values to display format
        hire_status = "RECOMMENDED" if frontend_hire_status else "NOT RECOMMENDED"
        hire_status_color = "#28a745" if frontend_hire_status else "#dc3545"
        
        # Frontend shows score as X/10 format
        display_score = f"{frontend_total_score:.1f}/10"
        
        print(f"\n🎯 FRONTEND DATA MATCH:")
        print(f"   AI Hire Recommendation: {frontend_hire_status}")
        print(f"   AI Total Score (0-10): {frontend_total_score}")
        print(f"   Display Score: {display_score}")
        print(f"   Hire Status: {hire_status}")
        print(f"   Skills Assessment Score: {overall_score}% (for matrix only)")
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
            'coding_questions': coding_questions,
            'code_submissions': code_submissions,
            'ai_analysis': ai_analysis,
            'section_scores_data': section_scores_data,
            'technical_metrics': technical_metrics,
            'coding_metrics': coding_metrics,
            'skills_assessment': skills_assessment,
            'overall_score': overall_score,
            'overall_level': overall_level,
            'overall_color': overall_color,
            'hire_status': hire_status,
            'hire_status_color': hire_status_color,
            'display_score': display_score,  # Frontend format: X/10
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
