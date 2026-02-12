from django.core.mail import send_mail
from django.conf import settings

print('📧 Sending Test Email to paturkardhananjay9075@gmail.com')
print('=' * 60)

subject = '🎯 AI Interviewer - Email Test Successful'
recipient = 'paturkardhananjay9075@gmail.com'

html_content = '''
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; }
        .btn { background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }
        .success-box { background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Interviewer System</h1>
        <p>✅ Email Test Successful</p>
    </div>
    
    <div class="content">
        <h2>🎉 Email Configuration Test Complete!</h2>
        <p>This email confirms that the AI Interviewer email system is working correctly.</p>
        
        <div class="success-box">
            <h3>✅ Test Results:</h3>
            <ul>
                <li><strong>Email Backend:</strong> ''' + str(settings.EMAIL_BACKEND) + '''</li>
                <li><strong>From Email:</strong> ''' + str(settings.DEFAULT_FROM_EMAIL) + '''</li>
                <li><strong>Recipient:</strong> ''' + recipient + '''</li>
                <li><strong>Status:</strong> Email sent successfully</li>
            </ul>
        </div>
        
        <h3>🔗 Test Interview Link:</h3>
        <a href="http://localhost:8000/interview/?session_key=test123456" class="btn">🎯 Access Interview Portal</a>
        <p><small>Session Key: <code>test123456</code></small></p>
    </div>
    
    <div class="footer">
        <p>🤖 AI Interviewer System | Email Test</p>
        <p>This is an automated test email. Please do not reply.</p>
    </div>
</body>
</html>
'''

text_content = '''AI Interviewer System - Email Test Successful

This email confirms that the AI Interviewer email system is working correctly.

Test Results:
- Email Backend: ''' + str(settings.EMAIL_BACKEND) + '''
- From Email: ''' + str(settings.DEFAULT_FROM_EMAIL) + '''
- Recipient: ''' + recipient + '''
- Status: Email sent successfully

Test Interview Link:
http://localhost:8000/interview/?session_key=test123456
Session Key: test123456

AI Interviewer System | Email Test
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
    print('✅ Professional test email sent successfully!')
    print('📧 To:', recipient)
    print('📧 Subject:', subject)
    print('🔗 From:', settings.DEFAULT_FROM_EMAIL)
    print('🎯 Interview Link Generated: http://localhost:8000/interview/?session_key=test123456')
except Exception as e:
    print('❌ Failed to send professional test email:', str(e))
