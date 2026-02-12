from django.core.mail import send_mail
from django.conf import settings

print('📧 Sending Test Email to paturkardhananjay4321@gmail.com')
print('=' * 60)

subject = '🧪 AI Interviewer - Test Email'
recipient = 'paturkardhananjay4321@gmail.com'

html_content = '''
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; }
        .btn { background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }
        .info-box { background: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Interviewer System</h1>
        <p>Email Configuration Test</p>
    </div>
    
    <div class="content">
        <h2>📧 Test Email Sent Successfully!</h2>
        <p>This is a test email to verify that the email system is working correctly.</p>
        
        <div class="info-box">
            <h3>📊 Configuration Details:</h3>
            <ul>
                <li><strong>Email Backend:</strong> ''' + str(settings.EMAIL_BACKEND) + '''</li>
                <li><strong>Email Host:</strong> ''' + str(settings.EMAIL_HOST) + '''</li>
                <li><strong>Email Port:</strong> ''' + str(settings.EMAIL_PORT) + '''</li>
                <li><strong>From Email:</strong> ''' + str(settings.DEFAULT_FROM_EMAIL) + '''</li>
                <li><strong>Use TLS:</strong> ''' + str(settings.EMAIL_USE_TLS) + '''</li>
                <li><strong>Use SSL:</strong> ''' + str(settings.EMAIL_USE_SSL) + '''</li>
            </ul>
        </div>
        
        <h3>🔗 Test Interview Link:</h3>
        <a href="http://localhost:8000/interview/?session_key=test123456" class="btn">🎯 Access Interview Portal</a>
        <p><small>Session Key: <code>test123456</code></small></p>
        
        <h3>✅ Email Features Working:</h3>
        <ul>
            <li>✅ HTML email rendering</li>
            <li>✅ Dynamic content insertion</li>
            <li>✅ Link generation</li>
            <li>✅ Professional styling</li>
        </ul>
    </div>
    
    <div class="footer">
        <p>🤖 AI Interviewer System | Test Email</p>
        <p>This is an automated test email. Please do not reply.</p>
    </div>
</body>
</html>
'''

text_content = '''Test Email from AI Interviewer System

Configuration Details:
- Email Backend: ''' + str(settings.EMAIL_BACKEND) + '''
- Email Host: ''' + str(settings.EMAIL_HOST) + '''
- Email Port: ''' + str(settings.EMAIL_PORT) + '''
- From Email: ''' + str(settings.DEFAULT_FROM_EMAIL) + '''

Test Interview Link:
http://localhost:8000/interview/?session_key=test123456

AI Interviewer System | Test Email
'''

try:
    send_mail(
        subject=subject,
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        html_message=html_content,
        fail_silently=False
    )
    print('✅ Test email sent successfully!')
    print('📧 To:', recipient)
    print('📧 Subject:', subject)
    print('🔗 From:', settings.DEFAULT_FROM_EMAIL)
except Exception as e:
    print('❌ Failed to send test email:', str(e))
    print('🔧 Please check your email configuration')
