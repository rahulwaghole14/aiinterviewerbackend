#!/usr/bin/env python
"""
Test email sending functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiinterviewer.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def test_email_configuration():
    """Test current email configuration"""
    print("📧 Email Configuration Test")
    print("=" * 50)
    
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Email Host: {settings.EMAIL_HOST}")
    print(f"Email Port: {settings.EMAIL_PORT}")
    print(f"Email Host User: {settings.EMAIL_HOST_USER}")
    print(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"Use SSL: {settings.EMAIL_USE_SSL}")
    
    # Check SendGrid configuration
    use_sendgrid = getattr(settings, 'USE_SENDGRID', False)
    sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
    
    print(f"Use SendGrid: {use_sendgrid}")
    print(f"SendGrid API Key: {'✅ Set' if sendgrid_api_key else '❌ Not set'}")
    
    return use_sendgrid, sendgrid_api_key

def send_test_email():
    """Send a test email"""
    print("\n📤 Sending Test Email")
    print("=" * 50)
    
    # Test recipient (you can change this)
    test_email = "test@example.com"  # Change this to your test email
    
    # Email content
    subject = "🧪 AI Interviewer - Test Email"
    
    html_content = """
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
                <li><strong>Email Backend:</strong> {email_backend}</li>
                <li><strong>Email Host:</strong> {email_host}</li>
                <li><strong>Email Port:</strong> {email_port}</li>
                <li><strong>From Email:</strong> {from_email}</li>
                <li><strong>Use TLS:</strong> {use_tls}</li>
                <li><strong>Use SSL:</strong> {use_ssl}</li>
            </ul>
            
            <h3>🔗 Test Interview Link:</h3>
            <p>Below is a sample interview link format:</p>
            <a href="{interview_url}" class="btn">🎯 Access Interview Portal</a>
            <p><small>Session Key: <code>{session_key}</code></small></p>
            
            <h3>✅ Email Features Working:</h3>
            <ul>
                <li>✅ HTML email rendering</li>
                <li>✅ Dynamic content insertion</li>
                <li>✅ Link generation</li>
                <li>✅ Professional styling</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>🤖 AI Interviewer System | Test Email | {timestamp}</p>
            <p>This is an automated test email. Please do not reply.</p>
        </div>
    </body>
    </html>
    """.format(
        email_backend=settings.EMAIL_BACKEND,
        email_host=settings.EMAIL_HOST,
        email_port=settings.EMAIL_PORT,
        from_email=settings.DEFAULT_FROM_EMAIL,
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=settings.EMAIL_USE_SSL,
        interview_url="http://localhost:8000/interview/?session_key=test123456",
        session_key="test123456",
        timestamp="2024-01-15 10:30:00"
    )
    
    # Plain text version
    text_content = strip_tags(html_content)
    
    try:
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            html_message=html_content,
            fail_silently=False
        )
        
        print(f"✅ Test email sent successfully to: {test_email}")
        print(f"📧 Subject: {subject}")
        print(f"🔗 From: {settings.DEFAULT_FROM_EMAIL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
        print(f"🔧 Please check your email configuration")
        return False

def send_interview_invite_test():
    """Send a test interview invite email"""
    print("\n📧 Sending Test Interview Invite")
    print("=" * 50)
    
    # Test data
    candidate_name = "Test Candidate"
    candidate_email = "test@example.com"  # Change this to your test email
    session_key = "test_invite_123456"
    scheduled_time = "2024-01-15 14:30:00"
    interview_url = f"http://localhost:8000/interview/?session_key={session_key}"
    
    # Email content
    subject = f"🎯 Interview Invitation - {candidate_name}"
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .footer {{ background: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; }}
            .btn {{ background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; font-size: 16px; }}
            .info-box {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; }}
            .warning-box {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Interviewer</h1>
            <p>Automated Interview System</p>
        </div>
        
        <div class="content">
            <h2>🎯 Interview Invitation</h2>
            <p>Dear <strong>{candidate_name}</strong>,</p>
            <p>You have been invited to participate in an AI-powered interview. Please find the details below:</p>
            
            <div class="info-box">
                <h3>📅 Interview Details:</h3>
                <ul>
                    <li><strong>Scheduled Time:</strong> {scheduled_time}</li>
                    <li><strong>Duration:</strong> Approximately 45-60 minutes</li>
                    <li><strong>Type:</strong> AI-powered video interview</li>
                </ul>
            </div>
            
            <div class="warning-box">
                <h3>⚠️ Important Instructions:</h3>
                <ul>
                    <li><strong>Access Window:</strong> Interview link is active 15 minutes before until 15 minutes after scheduled time</li>
                    <li><strong>Requirements:</strong> Working webcam, microphone, and stable internet connection</li>
                    <li><strong>Browser:</strong> Chrome, Firefox, or Safari (latest version recommended)</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{interview_url}" class="btn">🚀 Start Interview</a>
            </div>
            
            <h3>🔗 Interview Access:</h3>
            <p><strong>Interview Link:</strong> <a href="{interview_url}">{interview_url}</a></p>
            <p><strong>Session Key:</strong> <code>{session_key}</code></p>
            
            <h3>📋 What to Expect:</h3>
            <ul>
                <li>Technical and behavioral questions</li>
                <li>Coding challenges (if applicable)</li>
                <li>Real-time AI interaction</li>
                <li>Automated evaluation and feedback</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>🤖 AI Interviewer System | Interview Invitation</p>
            <p>This is an automated invitation. For technical support, please contact your recruiter.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = strip_tags(html_content)
    
    try:
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[candidate_email],
            html_message=html_content,
            fail_silently=False
        )
        
        print(f"✅ Interview invite sent successfully to: {candidate_email}")
        print(f"📧 Subject: {subject}")
        print(f"🔗 Interview URL: {interview_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send interview invite: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Email Testing Suite")
    print("=" * 60)
    
    # Test configuration
    use_sendgrid, sendgrid_key = test_email_configuration()
    
    # Send test email
    success1 = send_test_email()
    
    # Send interview invite test
    success2 = send_interview_invite_test()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"Test Email: {'✅ Success' if success1 else '❌ Failed'}")
    print(f"Interview Invite: {'✅ Success' if success2 else '❌ Failed'}")
    
    if success1 and success2:
        print("\n🎉 All email tests passed successfully!")
    else:
        print("\n⚠️ Some email tests failed. Please check your configuration.")
        
    print("\n📧 Email Configuration Guide:")
    print("- For SendGrid: Set USE_SENDGRID=true and SENDGRID_API_KEY")
    print("- For SMTP: Set EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD")
    print("- For Console: Default EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")
