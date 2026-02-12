from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

print('📧 Email Configuration Test')
print('=' * 50)
print(f'Email Backend: {settings.EMAIL_BACKEND}')
print(f'Email Host: {settings.EMAIL_HOST}')
print(f'Email Port: {settings.EMAIL_PORT}')
print(f'Email Host User: {settings.EMAIL_HOST_USER}')
print(f'Default From Email: {settings.DEFAULT_FROM_EMAIL}')
print(f'Use TLS: {settings.EMAIL_USE_TLS}')
print(f'Use SSL: {settings.EMAIL_USE_SSL}')

use_sendgrid = getattr(settings, 'USE_SENDGRID', False)
sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
print(f'Use SendGrid: {use_sendgrid}')
print(f'SendGrid API Key: {"✅ Set" if sendgrid_api_key else "❌ Not set"}')

print('\n📤 Sending Test Email')
print('=' * 50)

subject = '🧪 AI Interviewer - Test Email'
test_email = 'test@example.com'

html_content = '''
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; }
        .btn { background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Interviewer System</h1>
        <p>Test Email - Email Configuration Verification</p>
    </div>
    
    <div class="content">
        <h2>📧 Test Email Sent Successfully!</h2>
        <p>This is a test email to verify that the email system is working correctly.</p>
        
        <h3>📊 Configuration Details:</h3>
        <ul>
            <li><strong>Email Backend:</strong> ''' + str(settings.EMAIL_BACKEND) + '''</li>
            <li><strong>Email Host:</strong> ''' + str(settings.EMAIL_HOST) + '''</li>
            <li><strong>Email Port:</strong> ''' + str(settings.EMAIL_PORT) + '''</li>
            <li><strong>From Email:</strong> ''' + str(settings.DEFAULT_FROM_EMAIL) + '''</li>
            <li><strong>Use TLS:</strong> ''' + str(settings.EMAIL_USE_TLS) + '''</li>
            <li><strong>Use SSL:</strong> ''' + str(settings.EMAIL_USE_SSL) + '''</li>
        </ul>
        
        <h3>🔗 Test Interview Link:</h3>
        <a href="http://localhost:8000/interview/?session_key=test123456" class="btn">🎯 Access Interview Portal</a>
        <p><small>Session Key: <code>test123456</code></small></p>
    </div>
    
    <div class="footer">
        <p>🤖 AI Interviewer System | Test Email</p>
        <p>This is an automated test email. Please do not reply.</p>
    </div>
</body>
</html>
'''

text_content = strip_tags(html_content)

try:
    send_mail(
        subject=subject,
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test_email],
        html_message=html_content,
        fail_silently=False
    )
    print(f'✅ Test email sent successfully to: {test_email}')
    print(f'📧 Subject: {subject}')
    print(f'🔗 From: {settings.DEFAULT_FROM_EMAIL}')
except Exception as e:
    print(f'❌ Failed to send test email: {str(e)}')
    print(f'🔧 Please check your email configuration')
