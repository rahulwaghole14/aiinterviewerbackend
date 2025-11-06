#!/usr/bin/env python
"""
Interactive script to help set up email host password for the AI Interview Portal.

This script will guide you through:
1. Choosing your email provider
2. Generating/entering your email password
3. Testing the configuration
4. Creating/updating .env file

Run: python setup_email_password.py
"""

import os
import sys
import getpass


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(number, text):
    """Print a formatted step."""
    print(f"\n[Step {number}] {text}")
    print("-" * 60)


def get_email_provider():
    """Ask user to select email provider."""
    print("\nSelect your email provider:")
    print("1. Gmail (Google)")
    print("2. Outlook / Microsoft 365")
    print("3. Yahoo Mail")
    print("4. SendGrid")
    print("5. AWS SES")
    print("6. Other (Custom SMTP)")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    return choice


def get_gmail_config():
    """Get Gmail configuration from user."""
    print("\n📧 Gmail Configuration")
    print("\n⚠️  IMPORTANT: You need a Google App Password, not your regular password!")
    print("\nTo generate a Google App Password:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Enable 2-Step Verification if not already enabled")
    print("3. Select 'Mail' and your device")
    print("4. Generate and copy the 16-character password")
    
    email = input("\nEnter your Gmail address: ").strip()
    password = getpass.getpass("Enter your Google App Password (16 characters): ").strip()
    
    config = {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.gmail.com",
        "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "True",
        "EMAIL_USE_SSL": "False",
        "EMAIL_HOST_USER": email,
        "EMAIL_HOST_PASSWORD": password,
        "DEFAULT_FROM_EMAIL": email,
    }
    return config


def get_outlook_config():
    """Get Outlook/Microsoft 365 configuration from user."""
    print("\n📧 Outlook / Microsoft 365 Configuration")
    print("\nTo generate an App Password:")
    print("1. Go to: https://account.microsoft.com/security")
    print("2. Enable Two-step verification")
    print("3. Go to App passwords and generate one for Mail")
    
    email = input("\nEnter your Outlook email: ").strip()
    password = getpass.getpass("Enter your App Password: ").strip()
    
    config = {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.office365.com",
        "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "True",
        "EMAIL_USE_SSL": "False",
        "EMAIL_HOST_USER": email,
        "EMAIL_HOST_PASSWORD": password,
        "DEFAULT_FROM_EMAIL": email,
    }
    return config


def get_yahoo_config():
    """Get Yahoo Mail configuration from user."""
    print("\n📧 Yahoo Mail Configuration")
    print("\nTo generate an App Password:")
    print("1. Go to: https://login.yahoo.com/account/security")
    print("2. Enable Two-step verification")
    print("3. Generate an App Password")
    
    email = input("\nEnter your Yahoo email: ").strip()
    password = getpass.getpass("Enter your App Password: ").strip()
    
    config = {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.mail.yahoo.com",
        "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "True",
        "EMAIL_USE_SSL": "False",
        "EMAIL_HOST_USER": email,
        "EMAIL_HOST_PASSWORD": password,
        "DEFAULT_FROM_EMAIL": email,
    }
    return config


def get_sendgrid_config():
    """Get SendGrid configuration from user."""
    print("\n📧 SendGrid Configuration")
    print("\n1. Create account at: https://sendgrid.com/")
    print("2. Go to Settings → API Keys")
    print("3. Create API Key with 'Mail Send' permissions")
    
    api_key = getpass.getpass("\nEnter your SendGrid API Key: ").strip()
    from_email = input("Enter your verified sender email: ").strip()
    
    config = {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.sendgrid.net",
        "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "True",
        "EMAIL_USE_SSL": "False",
        "EMAIL_HOST_USER": "apikey",
        "EMAIL_HOST_PASSWORD": api_key,
        "DEFAULT_FROM_EMAIL": from_email,
    }
    return config


def get_aws_ses_config():
    """Get AWS SES configuration from user."""
    print("\n📧 AWS SES Configuration")
    print("\n1. Setup AWS SES at: https://aws.amazon.com/ses/")
    print("2. Go to SES Console → SMTP Settings")
    print("3. Create SMTP credentials")
    
    region = input("\nEnter your AWS region (e.g., us-east-1): ").strip()
    username = input("Enter your SMTP username: ").strip()
    password = getpass.getpass("Enter your SMTP password: ").strip()
    from_email = input("Enter your verified sender email: ").strip()
    
    config = {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": f"email-smtp.{region}.amazonaws.com",
        "EMAIL_PORT": "587",
        "EMAIL_USE_TLS": "True",
        "EMAIL_USE_SSL": "False",
        "EMAIL_HOST_USER": username,
        "EMAIL_HOST_PASSWORD": password,
        "DEFAULT_FROM_EMAIL": from_email,
    }
    return config


def get_custom_config():
    """Get custom SMTP configuration from user."""
    print("\n📧 Custom SMTP Configuration")
    
    host = input("Enter SMTP host (e.g., smtp.example.com): ").strip()
    port = input("Enter SMTP port (587 for TLS, 465 for SSL): ").strip()
    use_tls = input("Use TLS? (y/n): ").strip().lower() == "y"
    use_ssl = input("Use SSL? (y/n): ").strip().lower() == "y"
    username = input("Enter SMTP username/email: ").strip()
    password = getpass.getpass("Enter SMTP password: ").strip()
    from_email = input("Enter default from email: ").strip()
    
    config = {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": host,
        "EMAIL_PORT": port,
        "EMAIL_USE_TLS": "True" if use_tls else "False",
        "EMAIL_USE_SSL": "True" if use_ssl else "False",
        "EMAIL_HOST_USER": username,
        "EMAIL_HOST_PASSWORD": password,
        "DEFAULT_FROM_EMAIL": from_email,
    }
    return config


def write_env_file(config, env_file=".env"):
    """Write configuration to .env file."""
    print(f"\n📝 Writing configuration to {env_file}...")
    
    # Read existing .env if it exists
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            existing_lines = f.readlines()
    
    # Keep non-email related variables
    email_keys = ["EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_USE_TLS", 
                  "EMAIL_USE_SSL", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "DEFAULT_FROM_EMAIL"]
    
    filtered_lines = []
    for line in existing_lines:
        if not any(line.strip().startswith(key + "=") for key in email_keys):
            filtered_lines.append(line)
    
    # Add email configuration
    with open(env_file, "w") as f:
        f.writelines(filtered_lines)
        f.write("\n# Email Configuration\n")
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Configuration written to {env_file}")


def set_environment_variables(config):
    """Set environment variables in current session."""
    print("\n🔧 Setting environment variables for current session...")
    for key, value in config.items():
        os.environ[key] = value
        print(f"   {key}={value[:20] + '...' if len(value) > 20 else value}")
    print("✅ Environment variables set")


def test_email_config(config):
    """Test email configuration."""
    print("\n🧪 Testing email configuration...")
    
    # Set environment variables for testing
    for key, value in config.items():
        os.environ[key] = value
    
    # Try to import Django and test
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
        import django
        django.setup()
        
        from django.conf import settings
        from django.core.mail import get_connection
        
        print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"   Testing connection...")
        
        conn = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL,
            fail_silently=False,
        )
        conn.open()
        conn.close()
        print("✅ Connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\n⚠️  Don't worry! You can still use the configuration.")
        print("   The error might be due to network or provider-specific requirements.")
        print("   Try running 'python test_email.py' to test with actual email sending.")
        return False


def main():
    """Main function."""
    print_header("Email Password Setup for AI Interview Portal")
    
    print("This script will help you configure email settings for your Django application.")
    print("\nYou'll need:")
    print("  • Your email provider's SMTP credentials")
    print("  • An App Password (for Gmail/Outlook/Yahoo) or API key (for SendGrid)")
    
    proceed = input("\nReady to start? (y/n): ").strip().lower()
    if proceed != "y":
        print("Setup cancelled.")
        return
    
    # Get provider choice
    provider = get_email_provider()
    
    # Get configuration based on provider
    config = None
    if provider == "1":
        config = get_gmail_config()
    elif provider == "2":
        config = get_outlook_config()
    elif provider == "3":
        config = get_yahoo_config()
    elif provider == "4":
        config = get_sendgrid_config()
    elif provider == "5":
        config = get_aws_ses_config()
    elif provider == "6":
        config = get_custom_config()
    else:
        print("Invalid choice. Exiting.")
        return
    
    # Review configuration
    print("\n📋 Configuration Summary:")
    print("-" * 60)
    for key, value in config.items():
        if "PASSWORD" in key:
            print(f"   {key}={'*' * min(len(value), 20)}")
        else:
            print(f"   {key}={value}")
    
    confirm = input("\n✅ Save this configuration? (y/n): ").strip().lower()
    if confirm != "y":
        print("Configuration not saved.")
        return
    
    # Write to .env file
    write_env_file(config)
    
    # Set environment variables
    set_environment_variables(config)
    
    # Test configuration
    test_config = input("\n🧪 Test email configuration now? (y/n): ").strip().lower()
    if test_config == "y":
        test_email_config(config)
    
    # Final instructions
    print_header("Setup Complete!")
    print("✅ Email configuration has been saved to .env file")
    print("\n📝 Next Steps:")
    print("   1. The configuration is saved in .env file")
    print("   2. Make sure .env is in your .gitignore (never commit passwords!)")
    print("   3. Test your email: python test_email.py")
    print("   4. Restart your Django server if it's running")
    print("\n📚 For more information, see: EMAIL_HOST_PASSWORD_GUIDE.md")
    
    if not os.path.exists(".gitignore"):
        create_gitignore = input("\n⚠️  Create .gitignore to protect .env file? (y/n): ").strip().lower()
        if create_gitignore == "y":
            with open(".gitignore", "w") as f:
                f.write("# Environment variables\n.env\n.env.local\n\n")
            print("✅ .gitignore created")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

