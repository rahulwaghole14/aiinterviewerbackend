#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from django.contrib.auth.hashers import make_password, check_password, get_hasher
from django.conf import settings
from authapp.models import CustomUser


def check_password_security():
    """Check and demonstrate password security features"""

    print("🔐 Password Security Analysis")
    print("=" * 50)

    # Check current password hasher
    print("\n📋 Current Password Hasher Configuration:")
    print(f"   - Default Hasher: {settings.PASSWORD_HASHERS[0]}")
    print(f"   - Available Hashers: {len(settings.PASSWORD_HASHERS)}")

    for i, hasher in enumerate(settings.PASSWORD_HASHERS):
        print(f"   {i+1}. {hasher}")

    # Test password hashing
    print("\n🔒 Password Hashing Demonstration:")
    test_password = "password123"

    # Hash the password
    hashed_password = make_password(test_password)
    print(f"   - Original Password: {test_password}")
    print(f"   - Hashed Password: {hashed_password}")
    print(f"   - Hash Length: {len(hashed_password)} characters")

    # Verify the password
    is_valid = check_password(test_password, hashed_password)
    print(f"   - Password Verification: {'✅ Valid' if is_valid else '❌ Invalid'}")

    # Test with wrong password
    wrong_password = "wrongpassword"
    is_wrong_valid = check_password(wrong_password, hashed_password)
    print(
        f"   - Wrong Password Test: {'❌ Should be invalid' if not is_wrong_valid else '⚠️  Security issue!'}"
    )

    # Check if hash includes salt
    if hashed_password.startswith("pbkdf2_sha256$"):
        print(f"   - ✅ Uses PBKDF2 with SHA256 (industry standard)")
        print(f"   - ✅ Includes salt for additional security")
    elif hashed_password.startswith("bcrypt$"):
        print(f"   - ✅ Uses bcrypt (very secure)")
    else:
        print(f"   - ⚠️  Using older hashing method")


def check_user_password_security():
    """Check password security for existing users"""

    print("\n👥 User Password Security Check:")
    print("=" * 50)

    users = CustomUser.objects.all()
    print(f"Total users: {users.count()}")

    secure_count = 0
    insecure_count = 0

    for user in users:
        # Get the password field (this shows the hash, not the actual password)
        password_field = user.password

        if password_field.startswith("pbkdf2_sha256$"):
            secure_count += 1
            status = "✅ Secure"
        elif password_field.startswith("bcrypt$"):
            secure_count += 1
            status = "✅ Very Secure"
        elif password_field.startswith("sha1$"):
            insecure_count += 1
            status = "❌ Insecure (SHA1)"
        elif password_field.startswith("md5$"):
            insecure_count += 1
            status = "❌ Very Insecure (MD5)"
        else:
            insecure_count += 1
            status = "⚠️  Unknown"

        print(f"   - {user.email}: {status}")

    print(f"\n📊 Security Summary:")
    print(f"   - Secure passwords: {secure_count}")
    print(f"   - Insecure passwords: {insecure_count}")
    print(
        f"   - Security rate: {(secure_count/(secure_count+insecure_count)*100):.1f}%"
    )


def demonstrate_password_upgrade():
    """Demonstrate upgrading passwords to more secure hashers"""

    print("\n🔄 Password Upgrade Demonstration:")
    print("=" * 50)

    # Create a test user with a simple password
    test_email = "security_test@example.com"

    try:
        user = CustomUser.objects.get(email=test_email)
        print(f"   - Using existing test user: {user.email}")
    except CustomUser.DoesNotExist:
        user = CustomUser.objects.create_user(
            username=test_email,
            email=test_email,
            password="testpass123",
            full_name="Security Test User",
            role="ADMIN",
        )
        print(f"   - Created test user: {user.email}")

    # Check current hash
    old_hash = user.password
    print(f"   - Current hash: {old_hash[:50]}...")

    # Upgrade password (this happens automatically when user logs in)
    # But we can also force it
    user.set_password("testpass123")
    user.save()

    new_hash = user.password
    print(f"   - New hash: {new_hash[:50]}...")

    # Verify both hashes work
    old_valid = check_password("testpass123", old_hash)
    new_valid = check_password("testpass123", new_hash)

    print(f"   - Old hash still valid: {'✅ Yes' if old_valid else '❌ No'}")
    print(f"   - New hash valid: {'✅ Yes' if new_valid else '❌ No'}")


def recommend_security_improvements():
    """Recommend security improvements"""

    print("\n💡 Security Recommendations:")
    print("=" * 50)

    print("1. ✅ Current Setup is Good:")
    print("   - Django uses PBKDF2 with SHA256 by default")
    print("   - Passwords are properly hashed, not encrypted")
    print("   - Salt is automatically added to each password")

    print("\n2. 🔧 Optional Improvements:")
    print("   - Consider using bcrypt for even better security")
    print("   - Implement password complexity requirements")
    print("   - Add rate limiting for login attempts")
    print("   - Enable two-factor authentication (2FA)")

    print("\n3. 🛡️ Additional Security Measures:")
    print("   - Use HTTPS in production")
    print("   - Implement session timeout")
    print("   - Log failed login attempts")
    print("   - Regular security audits")


if __name__ == "__main__":
    print("🚀 Password Security Analysis")
    print("=" * 60)

    check_password_security()
    check_user_password_security()
    demonstrate_password_upgrade()
    recommend_security_improvements()

    print("\n✅ Analysis completed!")
    print("\n🔐 Key Points:")
    print("   - Passwords are HASHED, not encrypted")
    print("   - Django uses industry-standard PBKDF2")
    print("   - Each password has a unique salt")
    print("   - Passwords cannot be 'decrypted' back to plain text")
