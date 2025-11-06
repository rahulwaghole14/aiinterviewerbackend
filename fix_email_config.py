#!/usr/bin/env python
"""
Fix email configuration - checks and helps configure .env file
"""
import os
import sys

def check_and_fix_email_config():
    """Check email configuration and provide fix instructions"""
    print("\n" + "=" * 70)
    print("  Email Configuration Checker & Fixer")
    print("=" * 70 + "\n")
    
    # Try to load .env
    from dotenv import load_dotenv, set_key, find_dotenv
    
    env_path = find_dotenv()
    if not env_path:
        # Try to find .env in project root
        env_path = os.path.join(os.getcwd(), '.env')
        if not os.path.exists(env_path):
            print("[ERROR] .env file not found!")
            print(f"Expected location: {env_path}")
            print("\nPlease create a .env file in the project root with:")
            print("EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
            print("EMAIL_HOST=smtp.gmail.com")
            print("EMAIL_PORT=587")
            print("EMAIL_USE_TLS=True")
            print("EMAIL_USE_SSL=False")
            print("EMAIL_HOST_USER=your-email@gmail.com")
            print("EMAIL_HOST_PASSWORD=your-app-password")
            print("DEFAULT_FROM_EMAIL=your-email@gmail.com")
            return False
    
    load_dotenv(env_path)
    
    print(f"Checking .env file: {env_path}\n")
    
    issues = []
    fixes_needed = []
    
    email_backend = os.getenv('EMAIL_BACKEND', '').strip()
    email_host = os.getenv('EMAIL_HOST', '').strip()
    email_user = os.getenv('EMAIL_HOST_USER', '').strip()
    email_password = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
    email_port = os.getenv('EMAIL_PORT', '').strip()
    email_tls = os.getenv('EMAIL_USE_TLS', '').strip()
    email_ssl = os.getenv('EMAIL_USE_SSL', '').strip()
    
    # Check EMAIL_BACKEND
    if not email_backend or 'console' in email_backend.lower():
        issues.append("EMAIL_BACKEND is not set or set to 'console' - emails won't be sent!")
        fixes_needed.append(('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'))
    else:
        print(f"[OK] EMAIL_BACKEND: {email_backend}")
    
    # Check EMAIL_HOST
    if not email_host:
        issues.append("EMAIL_HOST is not set!")
        fixes_needed.append(('EMAIL_HOST', 'smtp.gmail.com'))
    else:
        print(f"[OK] EMAIL_HOST: {email_host}")
    
    # Check EMAIL_HOST_USER
    if not email_user:
        issues.append("EMAIL_HOST_USER is not set!")
        fixes_needed.append(('EMAIL_HOST_USER', 'your-email@gmail.com'))
    else:
        print(f"[OK] EMAIL_HOST_USER: {email_user[:20]}...")
    
    # Check EMAIL_HOST_PASSWORD
    if not email_password:
        issues.append("EMAIL_HOST_PASSWORD is not set!")
        fixes_needed.append(('EMAIL_HOST_PASSWORD', 'your-app-password'))
    else:
        print(f"[OK] EMAIL_HOST_PASSWORD: Set (hidden)")
    
    # Check EMAIL_PORT
    if not email_port:
        issues.append("EMAIL_PORT is not set!")
        fixes_needed.append(('EMAIL_PORT', '587'))
    else:
        print(f"[OK] EMAIL_PORT: {email_port}")
    
    # Check EMAIL_USE_TLS
    if not email_tls or email_tls.lower() not in ['true', '1', 'yes']:
        if email_host == 'smtp.gmail.com' and email_port == '587':
            issues.append("EMAIL_USE_TLS should be True for Gmail with port 587")
            fixes_needed.append(('EMAIL_USE_TLS', 'True'))
    
    # CRITICAL: Check EMAIL_USE_SSL vs EMAIL_USE_TLS conflict
    email_tls_set = email_tls.lower() in ['true', '1', 'yes']
    email_ssl_set = email_ssl.lower() in ['true', '1', 'yes']
    
    if email_tls_set and email_ssl_set:
        # Both are True - this is invalid
        if email_port == '587':
            issues.append("Both EMAIL_USE_TLS and EMAIL_USE_SSL are True - TLS should be used for port 587 (disable SSL)")
            fixes_needed.append(('EMAIL_USE_SSL', 'False'))
        else:
            issues.append("Both EMAIL_USE_TLS and EMAIL_USE_SSL are True - they are mutually exclusive")
            # For port 465, use SSL; for port 587, use TLS
            if email_port == '465':
                fixes_needed.append(('EMAIL_USE_TLS', 'False'))
            else:
                fixes_needed.append(('EMAIL_USE_SSL', 'False'))
    
    print()
    
    if issues:
        print("ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\nAUTOMATIC FIX:")
        print("The following changes will be made to your .env file:")
        for key, value in fixes_needed:
            current = os.getenv(key, 'NOT SET')
            print(f"  {key}: '{current}' -> '{value}'")
        
        try:
            # Auto-apply fixes without prompting (non-interactive)
            print("\nApplying fixes automatically...")
            for key, value in fixes_needed:
                set_key(env_path, key, value)
            print(f"\n[SUCCESS] Updated .env file: {env_path}")
            print("\nIMPORTANT: Please restart your Django server for changes to take effect!")
            print("Restart command: Stop the server (Ctrl+C) and start it again.")
            return True
        except Exception as e:
            print(f"\n[ERROR] Could not update .env: {e}")
            print("\nPlease update .env manually with these values:")
            for key, value in fixes_needed:
                print(f"{key}={value}")
            return False
    else:
        print("[SUCCESS] All email settings are configured correctly!")
        print("\nTo test email sending, run:")
        print("  python test_email_credentials.py")
        return True

if __name__ == "__main__":
    try:
        check_and_fix_email_config()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

