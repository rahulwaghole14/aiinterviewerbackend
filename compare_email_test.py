from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

print('📧 Comparing Test Email vs Interview Email')
print('=' * 60)

recipient = 'paturkardhananjay9075@gmail.com'

# Test 1: Simple test email (the one that works)
print('\n🧪 Test 1: Simple Test Email (Working)')
print('-' * 40)
try:
    result1 = send_mail(
        'Simple Test Email',
        'This is the simple test email that works.',
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False
    )
    print(f'✅ Simple test result: {result1}')
except Exception as e:
    print(f'❌ Simple test failed: {e}')

# Test 2: HTML email (like interview scheduling)
print('\n🧪 Test 2: HTML Email (Like Interview Scheduling)')
print('-' * 40)
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
    
    # Method A: Using send_mail with HTML
    result2a = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        html_message=html_message,
        fail_silently=False
    )
    print(f'✅ HTML email (send_mail) result: {result2a}')
    
    # Method B: Using EmailMultiAlternatives (like interview scheduling)
    email = EmailMultiAlternatives(
        subject=subject,
        body=message,  # Plain text version
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient]
    )
    email.attach_alternative(html_message, "text/html")  # HTML version
    result2b = email.send(fail_silently=False)
    print(f'✅ HTML email (EmailMultiAlternatives) result: {result2b}')
    
except Exception as e:
    print(f'❌ HTML email failed: {e}')
    import traceback
    traceback.print_exc()

# Test 3: Check email configuration
print('\n🔧 Email Configuration:')
print('-' * 40)
print(f'Email Backend: {settings.EMAIL_BACKEND}')
print(f'Use SendGrid: {getattr(settings, "USE_SENDGRID", False)}')
print(f'SendGrid API Key: {"Set" if getattr(settings, "SENDGRID_API_KEY", "") else "Not set"}')
print(f'Default From: {settings.DEFAULT_FROM_EMAIL}')
print(f'Email Host: {settings.EMAIL_HOST}')
print(f'Email Port: {settings.EMAIL_PORT}')
print(f'Email User: {settings.EMAIL_HOST_USER}')
print(f'Use TLS: {settings.EMAIL_USE_TLS}')
print(f'Use SSL: {settings.EMAIL_USE_SSL}')

print('\n📊 Summary:')
print('=' * 30)
print('If Test 1 works but Test 2 fails, the issue is with HTML emails')
print('If both work, the issue is in interview scheduling logic')
print('If both fail, the issue is with email configuration')
