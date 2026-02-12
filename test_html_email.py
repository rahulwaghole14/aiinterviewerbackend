from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

recipient = 'paturkardhananjay9075@gmail.com'

print('📧 Testing HTML Email (like interview scheduling)')

try:
    subject = 'Interview Scheduled - Test Position at Test Company'
    message = '''Dear Candidate,

Your interview has been scheduled successfully!

Interview Details:
• Position: Test Position
• Company: Test Company
• Date & Time: TBD
• Duration: TBD
• Interview Type: AI Interview

Join Your Interview:
Click the link below to join your interview:
http://localhost:8000/interview/?session_key=test123456

Best regards,
Test Company'''
    
    html_message = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear Candidate,</p>
    
    <p>Your interview has been scheduled successfully!</p>
    
    <h3 style="color: #4a5568;">📋 Interview Details:</h3>
    <ul>
        <li><strong>Position:</strong> Test Position</li>
        <li><strong>Company:</strong> Test Company</li>
        <li><strong>Date & Time:</strong> TBD</li>
        <li><strong>Duration:</strong> TBD</li>
        <li><strong>Interview Type:</strong> AI Interview</li>
    </ul>
    
    <h3 style="color: #4a5568;">🔗 Join Your Interview:</h3>
    <p>Click the link below to join your interview at the scheduled time:</p>
    <p><a href="http://localhost:8000/interview/?session_key=test123456" style="color: #3182ce; text-decoration: underline;">http://localhost:8000/interview/?session_key=test123456</a></p>
    
    <p>Best regards,<br><br>
    <strong>Test Company</strong></p>
</body>
</html>'''
    
    # Test HTML email (like interview scheduling)
    result = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        html_message=html_message,
        fail_silently=False
    )
    print(f'✅ HTML email result: {result}')
    print(f'✅ HTML email sent successfully to {recipient}')
    
except Exception as e:
    print(f'❌ HTML email failed: {e}')
    import traceback
    traceback.print_exc()

print(f'Email Backend: {settings.EMAIL_BACKEND}')
print(f'Use SendGrid: {getattr(settings, "USE_SENDGRID", False)}')
