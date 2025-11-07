"""
Service to create Evaluation objects after interview completion
Includes AI analysis and proctoring warnings with snapshots
"""
import json
from django.utils import timezone
from interview_app.models import InterviewSession, WarningLog, InterviewQuestion, CodeSubmission
from evaluation.models import Evaluation
from interviews.models import Interview


def create_evaluation_from_session(session_key: str):
    """
    Create Evaluation object from InterviewSession after interview completion
    Includes AI analysis and proctoring warnings with snapshots
    
    Args:
        session_key (str): The interview session key
        
    Returns:
        Evaluation: Created evaluation object
    """
    try:
        # Get the interview session
        session = InterviewSession.objects.get(session_key=session_key)
        
        # Find the Interview object linked to this session
        try:
            interview = Interview.objects.get(session_key=session_key)
        except Interview.DoesNotExist:
            # Try to find by candidate email
            if session.candidate_email:
                try:
                    from candidates.models import Candidate
                    candidate = Candidate.objects.get(email=session.candidate_email)
                    interview = Interview.objects.filter(candidate=candidate).order_by('-created_at').first()
                except:
                    interview = None
            
            if not interview:
                print(f"⚠️ No Interview found for session {session_key}, skipping evaluation creation")
                return None
        
        # Check if evaluation already exists (using try-except to avoid database errors)
        existing_evaluation = None
        try:
            existing_evaluation = Evaluation.objects.get(interview=interview)
            print(f"🔍 Evaluation already exists for interview {interview.id}")
            
            # Check if details field is empty or missing ai_analysis
            needs_update = False
            if not existing_evaluation.details or not isinstance(existing_evaluation.details, dict):
                print(f"   ⚠️ Existing evaluation has empty details, will update...")
                needs_update = True
            elif 'ai_analysis' not in existing_evaluation.details or not existing_evaluation.details.get('ai_analysis'):
                print(f"   ⚠️ Existing evaluation missing ai_analysis, will update...")
                needs_update = True
            
            if needs_update:
                print(f"   🔄 Updating existing evaluation with details...")
                # Continue to generate details and update the evaluation
            else:
                print(f"   ✅ Existing evaluation has complete details, returning it")
                # Update Interview status to 'completed' if not already set
                if interview.status != Interview.Status.COMPLETED:
                    interview.status = Interview.Status.COMPLETED
                    interview.save(update_fields=['status'])
                    print(f"✅ Interview {interview.id} status updated to 'completed'")
                return existing_evaluation
                
        except Evaluation.DoesNotExist:
            print(f"🔍 No existing evaluation found, will create new one")
            pass  # Continue to create new evaluation
        except Exception as e:
            print(f"⚠️ Error checking existing evaluation: {e}")
            # Continue to create new evaluation
        
        # Get proctoring warnings with snapshots
        warning_logs = WarningLog.objects.filter(session=session).order_by('timestamp')
        proctoring_warnings = []
        for log in warning_logs:
            snapshot_url = None
            if log.snapshot:
                from django.conf import settings
                snapshot_url = f"{settings.MEDIA_URL}proctoring_snaps/{log.snapshot}"
            
            proctoring_warnings.append({
                'warning_type': log.warning_type,
                'timestamp': log.timestamp.isoformat(),
                'snapshot': log.snapshot,
                'snapshot_url': snapshot_url,
                'display_name': log.warning_type.replace('_', ' ').title()
            })
        
        # Import settings for PDF generation
        from django.conf import settings
        
        # Use comprehensive evaluation service for proper AI analysis
        try:
            from interview_app_11.comprehensive_evaluation_service import ComprehensiveEvaluationService
            comprehensive_service = ComprehensiveEvaluationService()
            print(f"🔄 Running comprehensive AI evaluation for session {session_key}")
            ai_evaluation_result = comprehensive_service.evaluate_complete_interview(session_key)
            
            # Extract comprehensive scores and feedback
            overall_score = ai_evaluation_result.get('overall_score', 50.0)
            technical_score = ai_evaluation_result.get('technical_score', 0)
            behavioral_score = ai_evaluation_result.get('behavioral_score', 0)
            coding_score = ai_evaluation_result.get('coding_score', 0)
            communication_score = ai_evaluation_result.get('communication_score', 0)
            
            # Build comprehensive traits
            traits = []
            if ai_evaluation_result.get('strengths'):
                traits.append(f"Strengths: {ai_evaluation_result['strengths']}")
            if ai_evaluation_result.get('weaknesses'):
                traits.append(f"Weaknesses: {ai_evaluation_result['weaknesses']}")
            if ai_evaluation_result.get('technical_analysis'):
                traits.append(f"Technical: {ai_evaluation_result['technical_analysis']}")
            if ai_evaluation_result.get('behavioral_analysis'):
                traits.append(f"Behavioral: {ai_evaluation_result['behavioral_analysis']}")
            if ai_evaluation_result.get('coding_analysis'):
                traits.append(f"Coding: {ai_evaluation_result['coding_analysis']}")
            
            # Build comprehensive suggestions
            suggestions = []
            if ai_evaluation_result.get('detailed_feedback'):
                suggestions.append(ai_evaluation_result['detailed_feedback'])
            if ai_evaluation_result.get('hiring_recommendation'):
                suggestions.append(f"\nHiring Recommendation: {ai_evaluation_result['hiring_recommendation']}")
            if ai_evaluation_result.get('recommendation'):
                suggestions.append(f"Recommendation: {ai_evaluation_result['recommendation']}")
            
            print(f"✅ Comprehensive AI evaluation completed: Overall Score = {overall_score:.1f}/100")
            
        except Exception as e:
            print(f"⚠️ Error in comprehensive evaluation, using fallback: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to session scores
            overall_score = session.overall_performance_score or 0.0
            if overall_score == 0:
                scores = []
                if session.answers_score:
                    scores.append(session.answers_score * 10)
                if session.resume_score:
                    scores.append(session.resume_score * 10)
                overall_score = sum(scores) / len(scores) if scores else 50.0
            
            traits = []
            if session.overall_performance_feedback:
                traits.append(session.overall_performance_feedback)
            if session.answers_feedback:
                traits.append(f"Technical Answers: {session.answers_feedback}")
            
            suggestions = []
            if session.behavioral_analysis:
                suggestions.append(session.behavioral_analysis)
            
            # Set default AI evaluation result
            ai_evaluation_result = {
                'overall_score': overall_score,
                'technical_score': 0,
                'behavioral_score': 0,
                'coding_score': 0,
                'strengths': 'Limited evaluation data available',
                'weaknesses': 'Limited evaluation data available',
                'technical_analysis': 'Basic technical assessment based on question responses',
                'behavioral_analysis': 'Basic behavioral assessment based on communication',
                'coding_analysis': 'Completed coding challenges',
                'detailed_feedback': 'Comprehensive evaluation was not available due to API limitations',
                'hiring_recommendation': 'Consider for further evaluation',
                'recommendation': 'MAYBE'
            }
        
        # Extract questions and answers for metrics calculation
        questions = InterviewQuestion.objects.filter(session=session).order_by('order')
        total_questions = questions.count()
        questions_with_answers = questions.exclude(transcribed_answer__isnull=True).exclude(transcribed_answer='').exclude(transcribed_answer='No answer provided')
        questions_attempted = questions_with_answers.count()
        
        # Calculate response times
        response_times = [q.response_time_seconds for q in questions_with_answers if q.response_time_seconds and q.response_time_seconds > 0]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        total_completion_time = sum(response_times) / 60.0 if response_times else 0  # Convert to minutes
        
        # Calculate accuracy - estimate from overall score if not available
        # If we have question-level correctness data, use it; otherwise estimate from score
        questions_correct = 0
        accuracy_percentage = 0
        
        # Try to get correctness from evaluation result or estimate from score
        if 'questions_correct' in ai_evaluation_result and ai_evaluation_result['questions_correct'] > 0:
            questions_correct = ai_evaluation_result['questions_correct']
        elif 'accuracy_percentage' in ai_evaluation_result and ai_evaluation_result['accuracy_percentage'] > 0:
            accuracy_percentage = ai_evaluation_result['accuracy_percentage']
            questions_correct = int((accuracy_percentage / 100) * questions_attempted) if questions_attempted > 0 else 0
        elif 'questions_attempted' in ai_evaluation_result and ai_evaluation_result['questions_attempted'] > 0:
            # Use the questions_attempted from AI evaluation if available
            questions_attempted = ai_evaluation_result['questions_attempted']
            if 'accuracy_percentage' in ai_evaluation_result:
                accuracy_percentage = ai_evaluation_result['accuracy_percentage']
                questions_correct = int((accuracy_percentage / 100) * questions_attempted) if questions_attempted > 0 else 0
            else:
                # Estimate from overall score (assuming 10/10 = 100% correct)
                score_ratio = overall_score / 100.0
                questions_correct = int(score_ratio * questions_attempted) if questions_attempted > 0 else 0
                accuracy_percentage = (questions_correct / questions_attempted * 100) if questions_attempted > 0 else 0
        else:
            # Estimate from overall score (assuming 10/10 = 100% correct)
            score_ratio = overall_score / 100.0
            questions_correct = int(score_ratio * questions_attempted) if questions_attempted > 0 else 0
            accuracy_percentage = (questions_correct / questions_attempted * 100) if questions_attempted > 0 else 0
        
        # Build technical_questions array with all question data for graphs
        technical_questions = []
        for q in questions:
            # Determine if answer is correct (estimate from score if not explicitly marked)
            is_correct = False
            if questions_attempted > 0:
                # Simple heuristic: distribute correct answers proportionally
                question_index = len(technical_questions)
                if question_index < questions_correct:
                    is_correct = True
            
            # For CODING questions, get answer from CodeSubmission, not transcribed_answer
            answer_text = 'No answer provided'
            if q.question_type == 'CODING':
                try:
                    code_submission = CodeSubmission.objects.filter(
                        session=session,
                        question_id=str(q.id)
                    ).order_by('-created_at').first()
                    if code_submission and code_submission.submitted_code:
                        answer_text = code_submission.submitted_code
                    else:
                        answer_text = 'No code submitted'
                except Exception as e:
                    print(f"⚠️ Error fetching CodeSubmission for question {q.id} in evaluation: {e}")
                    answer_text = 'No code submitted'
            else:
                # For TECHNICAL and BEHAVIORAL questions, use transcribed_answer
                answer_text = q.transcribed_answer or 'No answer provided'
            
            technical_questions.append({
                'question_text': q.question_text,
                'question_type': q.question_type or 'TECHNICAL',
                'order': q.order,
                'answer': answer_text,
                'response_time': q.response_time_seconds or 0,
                'is_correct': is_correct,
                'question_level': q.question_level or 'MAIN',
            })
        
        # Get problem solving score (average of technical and coding)
        problem_solving_score = (
            (ai_evaluation_result.get('technical_score', 0) + ai_evaluation_result.get('coding_score', 0)) / 2
            if (ai_evaluation_result.get('technical_score', 0) > 0 or ai_evaluation_result.get('coding_score', 0) > 0)
            else 0
        )
        
        # Create details JSON with comprehensive AI analysis, proctoring warnings, and graph data
        # Ensure all required fields are present for UI graphs
        details = {
            'ai_analysis': {
                'overall_score': overall_score,
                'technical_score': ai_evaluation_result.get('technical_score', 0),
                'behavioral_score': ai_evaluation_result.get('behavioral_score', 0),
                'coding_score': ai_evaluation_result.get('coding_score', 0),
                'communication_score': ai_evaluation_result.get('communication_score', 0),
                'problem_solving_score': problem_solving_score,
                'confidence_level': ai_evaluation_result.get('confidence_level', 0),
                'strengths': ai_evaluation_result.get('strengths', '') or '',
                'weaknesses': ai_evaluation_result.get('weaknesses', '') or '',
                'technical_analysis': ai_evaluation_result.get('technical_analysis', '') or '',
                'behavioral_analysis': ai_evaluation_result.get('behavioral_analysis', '') or '',
                'coding_analysis': ai_evaluation_result.get('coding_analysis', '') or '',
                'detailed_feedback': ai_evaluation_result.get('detailed_feedback', '') or '',
                'hiring_recommendation': ai_evaluation_result.get('hiring_recommendation', '') or '',
                'recommendation': ai_evaluation_result.get('recommendation', 'MAYBE') or 'MAYBE',
                # Graph data metrics - use AI evaluation data if available, otherwise use calculated
                'questions_attempted': ai_evaluation_result.get('questions_attempted', questions_attempted),
                'questions_correct': questions_correct,
                'total_questions': total_questions,
                'accuracy_percentage': ai_evaluation_result.get('accuracy_percentage', accuracy_percentage),
                'average_response_time': average_response_time,
                'total_completion_time': total_completion_time,
                # Legacy fields for backward compatibility
                'resume_score': session.resume_score * 10 if session.resume_score else None,
                'answers_score': session.answers_score * 10 if session.answers_score else None,
                'resume_feedback': session.resume_feedback or '',
                'answers_feedback': session.answers_feedback or '',
                'overall_feedback': session.overall_performance_feedback or '',
            },
            'technical_questions': technical_questions,  # All questions with answers for Q&A display
            'proctoring': {
                'total_warnings': len(proctoring_warnings),
                'warnings': proctoring_warnings or [],
                'warning_types': list(set([w['warning_type'] for w in proctoring_warnings])) if proctoring_warnings else [],
            }
        }
        
        # Generate proctoring PDF if warnings exist
        proctoring_pdf_path = None
        if proctoring_warnings:
            try:
                print(f"📋 Generating proctoring PDF for {len(proctoring_warnings)} warnings...")
                from evaluation.proctoring_pdf import generate_proctoring_pdf
                # Create temporary evaluation object for PDF generation
                # (We'll create the actual evaluation after PDF is generated)
                class TempEvaluation:
                    def __init__(self, interview, details):
                        self.interview = interview
                        self.details = details
                        self.created_at = timezone.now()
                
                temp_evaluation = TempEvaluation(interview, details)
                proctoring_pdf_path = generate_proctoring_pdf(temp_evaluation)
                if proctoring_pdf_path:
                    # Add PDF path to details
                    details['proctoring_pdf'] = proctoring_pdf_path
                    # Ensure MEDIA_URL doesn't have double slashes
                    media_url = settings.MEDIA_URL.rstrip('/')
                    pdf_path = proctoring_pdf_path.lstrip('/')
                    details['proctoring_pdf_url'] = f"{media_url}/{pdf_path}"
                    print(f"✅ Proctoring PDF generated: {proctoring_pdf_path}")
                    print(f"✅ Proctoring PDF URL: {details['proctoring_pdf_url']}")
                else:
                    print(f"⚠️ Proctoring PDF generation returned None")
            except Exception as e:
                print(f"⚠️ Error generating proctoring PDF: {e}")
                import traceback
                traceback.print_exc()
        
        # Ensure details is always a dict with required keys
        if not details or not isinstance(details, dict):
            details = {}
        
        # Ensure ai_analysis and proctoring keys exist
        if 'ai_analysis' not in details:
            details['ai_analysis'] = {}
        if 'proctoring' not in details:
            details['proctoring'] = {'total_warnings': 0, 'warnings': [], 'warning_types': []}
        
        # Create or update Evaluation object
        if existing_evaluation:
            # Update existing evaluation
            existing_evaluation.overall_score = overall_score / 10.0
            existing_evaluation.traits = '\n\n'.join(traits) if traits else existing_evaluation.traits or "Interview completed successfully."
            existing_evaluation.suggestions = '\n\n'.join(suggestions) if suggestions else existing_evaluation.suggestions or "Continue building on your technical skills."
            existing_evaluation.details = details
            existing_evaluation.save()
            evaluation = existing_evaluation
            print(f"✅ Updated existing evaluation for interview {interview.id}")
        else:
            # Create new evaluation
            evaluation = Evaluation.objects.create(
                interview=interview,
                overall_score=overall_score / 10.0,  # Convert to 0-10 scale for model
                traits='\n\n'.join(traits) if traits else "Interview completed successfully.",
                suggestions='\n\n'.join(suggestions) if suggestions else "Continue building on your technical skills.",
                details=details
            )
            print(f"✅ Created new evaluation for interview {interview.id}")
        
        # Verify details were saved correctly
        evaluation.refresh_from_db()
        if not evaluation.details or not isinstance(evaluation.details, dict):
            print(f"⚠️ WARNING: Evaluation details not saved correctly, updating...")
            evaluation.details = details
            evaluation.save(update_fields=['details'])
        else:
            # Verify required keys exist
            saved_details = evaluation.details
            needs_update = False
            if 'ai_analysis' not in saved_details:
                saved_details['ai_analysis'] = details.get('ai_analysis', {})
                needs_update = True
            if 'proctoring' not in saved_details:
                saved_details['proctoring'] = details.get('proctoring', {'total_warnings': 0, 'warnings': [], 'warning_types': []})
                needs_update = True
            if needs_update:
                print(f"⚠️ WARNING: Missing keys in saved details, updating...")
                evaluation.details = saved_details
                evaluation.save(update_fields=['details'])
        
        # Update Interview status to 'completed' if not already set
        if interview.status != Interview.Status.COMPLETED:
            interview.status = Interview.Status.COMPLETED
            interview.save(update_fields=['status'])
            print(f"✅ Interview {interview.id} status updated to 'completed'")
        
        print(f"✅ Evaluation created for interview {interview.id}")
        print(f"   - Overall Score: {overall_score:.1f}/100 ({overall_score / 10.0:.1f}/10)")
        print(f"   - Proctoring Warnings: {len(proctoring_warnings)}")
        print(f"   - Details Keys: {list(details.keys())}")
        print(f"   - AI Analysis Keys: {list(details.get('ai_analysis', {}).keys())}")
        print(f"   - Proctoring Keys: {list(details.get('proctoring', {}).keys())}")
        
        if proctoring_pdf_path:
            print(f"✅ Proctoring PDF saved at: {proctoring_pdf_path}")
            print(f"✅ Proctoring PDF URL: {details.get('proctoring_pdf_url')}")
            # Update the evaluation to ensure PDF URL is saved
            evaluation.details = details
            evaluation.save(update_fields=['details'])
            print(f"✅ Evaluation updated with PDF URL")
        else:
            print(f"⚠️ No proctoring PDF generated (warnings: {len(proctoring_warnings)})")
        
        return evaluation
        
    except Exception as e:
        print(f"⚠️ Error creating evaluation from session {session_key}: {e}")
        import traceback
        traceback.print_exc()
        return None

