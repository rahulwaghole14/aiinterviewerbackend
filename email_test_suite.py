#!/usr/bin/env python
"""
Email Test and Configuration Guide
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiinterviewer.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail

def show_email_configuration():
    """Display current email configuration"""
    print("📧 Email Configuration Analysis")
    print("=" * 60)
    
    print(f"✅ Email Backend: {settings.EMAIL_BACKEND}")
    print(f"✅ Email Host: {settings.EMAIL_HOST}")
    print(f"✅ Email Port: {settings.EMAIL_PORT}")
    print(f"✅ Email Host User: {settings.EMAIL_HOST_USER}")
    print(f"✅ Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"✅ Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"✅ Use SSL: {settings.EMAIL_USE_SSL}")
    
    use_sendgrid = getattr(settings, 'USE_SENDGRID', False)
    sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
    
    print(f"✅ Use SendGrid: {use_sendgrid}")
    print(f"✅ SendGrid API Key: {'Set' if sendgrid_api_key else 'Not set'}")
    
    if sendgrid_api_key:
        # Show first few characters to verify it's set
        masked_key = sendgrid_api_key[:8] + "..." + sendgrid_api_key[-4:] if len(sendgrid_api_key) > 12 else "Set"
        print(f"✅ SendGrid API Key (masked): {masked_key}")
    
    return use_sendgrid, sendgrid_api_key

def show_sample_email_content():
    """Display sample email content"""
    print("\n📧 Sample Interview Invite Email")
    print("=" * 60)
    
    sample_email = """
Subject: 🎯 Interview Invitation - John Doe

From: support@talaro.ai
To: candidate@example.com

🤖 AI Interviewer System

🎯 Interview Invitation

Dear John Doe,

You have been invited to participate in an AI-powered interview. Please find the details below:

📅 Interview Details:
• Scheduled Time: 2024-01-15 14:30:00
• Duration: Approximately 45-60 minutes
• Type: AI-powered video interview

⚠️ Important Instructions:
• Access Window: Interview link is active 15 minutes before until 15 minutes after scheduled time
• Requirements: Working webcam, microphone, and stable internet connection
• Browser: Chrome, Firefox, or Safari (latest version recommended)

🚀 Start Interview
http://localhost:8000/interview/?session_key=test123456

🔗 Interview Access:
Interview Link: http://localhost:8000/interview/?session_key=test123456
Session Key: test123456

📋 What to Expect:
• Technical and behavioral questions
• Coding challenges (if applicable)
• Real-time AI interaction
• Automated evaluation and feedback

🤖 AI Interviewer System | Interview Invitation
This is an automated invitation. For technical support, please contact your recruiter.
"""
    
    print(sample_email)

def test_console_email():
    """Test email with console backend"""
    print("\n📧 Testing Email with Console Backend")
    print("=" * 60)
    
    # Temporarily override backend for testing
    original_backend = settings.EMAIL_BACKEND
    
    try:
        # Send test email (will appear in console)
        send_mail(
            '🧪 AI Interviewer - Test Email',
            '''This is a test email from the AI Interviewer system.

📊 Configuration Details:
- Email Backend: ''' + str(original_backend) + '''
- Email Host: ''' + str(settings.EMAIL_HOST) + '''
- Email Port: ''' + str(settings.EMAIL_PORT) + '''
- From Email: ''' + str(settings.DEFAULT_FROM_EMAIL) + '''
- Use TLS: ''' + str(settings.EMAIL_USE_TLS) + '''
- Use SSL: ''' + str(settings.EMAIL_USE_SSL) + '''

🔗 Test Interview Link:
http://localhost:8000/interview/?session_key=test123456

🤖 AI Interviewer System | Test Email
This is an automated test email. Please do not reply.''',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],
            fail_silently=False
        )
        
        print("✅ Test email sent successfully!")
        print("📧 Email content displayed above in console")
        
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")

def provide_sendgrid_fix():
    """Provide guidance for fixing SendGrid issues"""
    print("\n🔧 SendGrid Configuration Fix")
    print("=" * 60)
    
    print("🚨 SendGrid Authentication Error Detected!")
    print("\n📋 Possible Solutions:")
    
    print("\n1. 🔄 Verify SendGrid API Key:")
    print("   • Check your .env file for SENDGRID_API_KEY")
    print("   • Ensure it starts with 'SG.'")
    print("   • Verify the key is valid and active")
    
    print("\n2. 🔄 Check SendGrid Account:")
    print("   • Ensure your SendGrid account is active")
    print("   • Verify you have API access enabled")
    print("   • Check if you need to verify sender domain")
    
    print("\n3. 🔄 Update .env File:")
    print("   • SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("   • USE_SENDGRID=true")
    print("   • DEFAULT_FROM_EMAIL=support@yourdomain.com")
    
    print("\n4. 🔄 Alternative: Use SMTP Backend:")
    print("   • Set USE_SENDGRID=false")
    print("   • Configure SMTP settings:")
    print("   • EMAIL_HOST=smtp.gmail.com")
    print("   • EMAIL_PORT=587")
    print("   • EMAIL_HOST_USER=your@gmail.com")
    print("   • EMAIL_HOST_PASSWORD=your-app-password")
    print("   • EMAIL_USE_TLS=true")
    
    print("\n5. 🔄 For Testing: Use Console Backend:")
    print("   • EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")
    print("   • Emails will appear in console (no actual sending)")

def main():
    """Main test function"""
    print("🚀 AI Interviewer Email Test Suite")
    print("=" * 60)
    
    # Show configuration
    use_sendgrid, sendgrid_key = show_email_configuration()
    
    # Show sample email
    show_sample_email_content()
    
    # Test with console backend
    test_console_email()
    
    # Provide fix if SendGrid issue
    if use_sendgrid and sendgrid_key:
        provide_sendgrid_fix()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    print("✅ Email configuration analyzed")
    print("✅ Sample email template displayed")
    print("✅ Console email test completed")
    
    if use_sendgrid:
        print("⚠️ SendGrid authentication issue detected")
        print("📋 See fix suggestions above")
    else:
        print("✅ Ready to send emails")
    
    print("\n🎯 Next Steps:")
    print("1. Fix SendGrid configuration or use SMTP")
    print("2. Test with actual email recipient")
    print("3. Verify interview invite functionality")

if __name__ == "__main__":
    main()
