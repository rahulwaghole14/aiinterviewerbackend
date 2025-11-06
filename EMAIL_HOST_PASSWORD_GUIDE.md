# Email Host Password Generation Guide

This guide explains how to generate an email host password for your AI Interview Portal application.

## Overview

Your Django application is configured to send emails via SMTP. The email password is stored in the `EMAIL_HOST_PASSWORD` environment variable in your `interview_app/settings.py`.

## For Gmail (Google App Password)

If you're using Gmail as your email provider, you need to generate an **App Password** (not your regular Gmail password).

### Step-by-Step Instructions:

#### 1. **Enable 2-Step Verification**
   - Go to your Google Account: https://myaccount.google.com/
   - Navigate to **Security** → **2-Step Verification**
   - Follow the prompts to enable 2-Step Verification (required for App Passwords)

#### 2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Or navigate: **Security** → **2-Step Verification** → **App passwords**
   - Select **App**: Choose "Mail" or "Other (Custom name)"
   - Select **Device**: Choose "Other (Custom name)" and enter "Django Interview Portal"
   - Click **Generate**

#### 3. **Copy the App Password**
   - Google will display a 16-character password (spaces are for readability, include all characters)
   - Example format: `abcd efgh ijkl mnop`
   - Copy this password (you can remove spaces or keep them - both work)

#### 4. **Configure in Your Project**
   
   **Option A: Environment Variable (Recommended)**
   
   Create a `.env` file in your project root (if it doesn't exist):
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

   **Option B: Windows Environment Variables**
   
   Set in PowerShell:
   ```powershell
   $env:EMAIL_HOST_PASSWORD="your-16-character-app-password"
   $env:EMAIL_HOST_USER="your-email@gmail.com"
   $env:EMAIL_HOST="smtp.gmail.com"
   $env:EMAIL_PORT="587"
   $env:EMAIL_USE_TLS="True"
   $env:EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
   $env:DEFAULT_FROM_EMAIL="your-email@gmail.com"
   ```

### Gmail SMTP Settings:
```
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = your-email@gmail.com
EMAIL_HOST_PASSWORD = your-app-password (16 characters)
```

---

## For Other Email Providers

### Outlook / Microsoft 365

1. **Generate App Password:**
   - Go to: https://account.microsoft.com/security
   - Enable **Two-step verification** if not already enabled
   - Navigate to **Security** → **App passwords**
   - Generate a new app password for "Mail"
   - Copy the password

2. **SMTP Settings:**
   ```bash
   EMAIL_HOST=smtp.office365.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   EMAIL_HOST_USER=your-email@outlook.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

### Yahoo Mail

1. **Generate App Password:**
   - Go to: https://login.yahoo.com/account/security
   - Enable **Two-step verification**
   - Generate an **App Password**
   - Copy the password

2. **SMTP Settings:**
   ```bash
   EMAIL_HOST=smtp.mail.yahoo.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   EMAIL_HOST_USER=your-email@yahoo.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

### SendGrid (Professional Email Service)

1. **Create Account:** https://sendgrid.com/
2. **Generate API Key:**
   - Go to **Settings** → **API Keys**
   - Create API Key with "Mail Send" permissions
   - Copy the API key

3. **SMTP Settings:**
   ```bash
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   DEFAULT_FROM_EMAIL=your-verified-sender@domain.com
   ```

### AWS SES (Amazon Simple Email Service)

1. **Setup AWS SES:** https://aws.amazon.com/ses/
2. **Create SMTP Credentials:**
   - Go to SES Console → **SMTP Settings**
   - Create SMTP credentials
   - Copy username and password

3. **SMTP Settings:**
   ```bash
   EMAIL_HOST=email-smtp.region.amazonaws.com  # Replace 'region' with your AWS region
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-smtp-username
   EMAIL_HOST_PASSWORD=your-smtp-password
   ```

---

## Testing Your Email Configuration

After setting up your email password, test it using the provided test script:

```bash
# Activate your virtual environment first
venv\Scripts\activate

# Run the email test script
python test_email.py
```

This will:
- Display your current email configuration
- Attempt to send a test email
- Show any errors if configuration is incorrect

---

## Security Best Practices

1. **Never commit passwords to version control**
   - Use `.env` files and add them to `.gitignore`
   - Never hardcode passwords in `settings.py`

2. **Use App Passwords instead of main passwords**
   - App passwords are more secure and can be revoked individually
   - If compromised, you can revoke without changing your main password

3. **Rotate passwords regularly**
   - Generate new app passwords periodically
   - Update environment variables when rotating

4. **Use environment-specific configurations**
   - Development: Console backend (prints emails to terminal)
   - Production: SMTP backend with secure credentials

---

## Troubleshooting

### Common Issues:

**Issue: "Authentication failed"**
- ✅ Verify you're using an App Password (not your regular password)
- ✅ Ensure 2-Step Verification is enabled (for Gmail)
- ✅ Check that the password doesn't have extra spaces

**Issue: "Connection refused"**
- ✅ Check `EMAIL_PORT` matches your provider's requirements
- ✅ Verify firewall isn't blocking port 587 or 465
- ✅ Try port 465 with `EMAIL_USE_SSL=True` and `EMAIL_USE_TLS=False`

**Issue: "SMTP server not found"**
- ✅ Verify `EMAIL_HOST` is correct for your provider
- ✅ Check your internet connection

**Issue: "Email sent but not received"**
- ✅ Check spam/junk folder
- ✅ Verify `DEFAULT_FROM_EMAIL` matches your `EMAIL_HOST_USER`
- ✅ For production, ensure sender email is verified with your provider

---

## Quick Reference

### Gmail (Most Common)
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char App Password
```

### Development Mode (No actual email sent)
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## Need Help?

If you encounter issues:
1. Check the error message from `test_email.py`
2. Verify all environment variables are set correctly
3. Ensure your email provider allows SMTP access
4. Check your provider's documentation for latest SMTP settings

---

## Additional Resources

- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [Google Account Security](https://myaccount.google.com/security)

