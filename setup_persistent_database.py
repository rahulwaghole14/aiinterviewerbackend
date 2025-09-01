#!/usr/bin/env python3
"""
Setup Persistent Database for Render Deployment
==============================================

This script helps set up proper database persistence for your Render deployment.
It creates necessary data and ensures your database is properly configured.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings_production')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from candidates.models import Candidate
from jobs.models import Job, Domain
from companies.models import Company
from interviews.models import Interview
from authapp.models import CustomUser

User = get_user_model()

def setup_admin_user():
    """Create admin user if not exists"""
    print("🔧 Setting up admin user...")
    
    try:
        admin_email = 'admin@rslsolution.com'
        admin_user = User.objects.filter(email=admin_email).first()
        
        if not admin_user:
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password='admin123',
                full_name='Admin User',
                role='ADMIN'
            )
            print(f"✅ Created admin user: {admin_user.email}")
        else:
            # Update password to ensure it's correct
            admin_user.set_password('admin123')
            admin_user.save()
            print(f"✅ Admin user already exists: {admin_user.email}")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None

def setup_test_users():
    """Create test users for different roles"""
    print("🔧 Setting up test users...")
    
    test_users = [
        {
            'email': 'company_test@example.com',
            'password': 'password123',
            'full_name': 'Company Test User',
            'role': 'COMPANY',
            'company_name': 'Test Company'
        },
        {
            'email': 'agency_test@example.com',
            'password': 'password123',
            'full_name': 'Agency Test User',
            'role': 'HIRING_AGENCY',
            'company_name': 'Test Agency'
        },
        {
            'email': 'recruiter_test@example.com',
            'password': 'password123',
            'full_name': 'Recruiter Test User',
            'role': 'RECRUITER',
            'company_name': 'Test Agency'
        }
    ]
    
    created_users = []
    for user_data in test_users:
        try:
            user = User.objects.filter(email=user_data['email']).first()
            if not user:
                user = User.objects.create_user(
                    email=user_data['email'],
                    password=user_data['password'],
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    company_name=user_data['company_name']
                )
                print(f"✅ Created {user_data['role']} user: {user.email}")
            else:
                print(f"✅ {user_data['role']} user already exists: {user.email}")
            created_users.append(user)
        except Exception as e:
            print(f"❌ Error creating {user_data['role']} user: {e}")
    
    return created_users

def setup_domains():
    """Create default domains"""
    print("🔧 Setting up domains...")
    
    domains = [
        'Technology',
        'Healthcare',
        'Finance',
        'Education',
        'Manufacturing',
        'Retail',
        'Consulting',
        'Marketing',
        'Sales',
        'Operations'
    ]
    
    created_domains = []
    for domain_name in domains:
        try:
            domain, created = Domain.objects.get_or_create(name=domain_name)
            if created:
                print(f"✅ Created domain: {domain.name}")
            else:
                print(f"✅ Domain already exists: {domain.name}")
            created_domains.append(domain)
        except Exception as e:
            print(f"❌ Error creating domain {domain_name}: {e}")
    
    return created_domains

def setup_companies():
    """Create test companies"""
    print("🔧 Setting up companies...")
    
    companies_data = [
        {
            'name': 'RSL Solutions',
            'description': 'Leading technology solutions provider',
            'industry': 'Technology',
            'website': 'https://rslsolutions.com',
            'phone': '+1-555-0123',
            'email': 'contact@rslsolutions.com'
        },
        {
            'name': 'TechCorp',
            'description': 'Innovative software development company',
            'industry': 'Technology',
            'website': 'https://techcorp.com',
            'phone': '+1-555-0456',
            'email': 'info@techcorp.com'
        }
    ]
    
    created_companies = []
    for company_data in companies_data:
        try:
            company, created = Company.objects.get_or_create(
                name=company_data['name'],
                defaults=company_data
            )
            if created:
                print(f"✅ Created company: {company.name}")
            else:
                print(f"✅ Company already exists: {company.name}")
            created_companies.append(company)
        except Exception as e:
            print(f"❌ Error creating company {company_data['name']}: {e}")
    
    return created_companies

def setup_jobs():
    """Create test jobs"""
    print("🔧 Setting up jobs...")
    
    jobs_data = [
        {
            'job_title': 'Software Engineer',
            'company_name': 'RSL Solutions',
            'spoc_email': 'spoc@rslsolutions.com',
            'hiring_manager_email': 'hm@rslsolutions.com',
            'number_to_hire': 2,
            'position_level': 'IC',
            'tech_stack_details': 'Python, Django, React, JavaScript, SQL, AWS, Docker',
            'job_description': 'We are looking for a skilled Software Engineer to join our dynamic team.'
        },
        {
            'job_title': 'Senior Developer',
            'company_name': 'TechCorp',
            'spoc_email': 'spoc@techcorp.com',
            'hiring_manager_email': 'hm@techcorp.com',
            'number_to_hire': 1,
            'position_level': 'IC',
            'tech_stack_details': 'Java, Spring Boot, Angular, PostgreSQL, Kubernetes',
            'job_description': 'Join our team as a Senior Developer and help build amazing products.'
        }
    ]
    
    created_jobs = []
    for job_data in jobs_data:
        try:
            job, created = Job.objects.get_or_create(
                job_title=job_data['job_title'],
                company_name=job_data['company_name'],
                defaults=job_data
            )
            if created:
                print(f"✅ Created job: {job.job_title} at {job.company_name}")
            else:
                print(f"✅ Job already exists: {job.job_title} at {job.company_name}")
            created_jobs.append(job)
        except Exception as e:
            print(f"❌ Error creating job {job_data['job_title']}: {e}")
    
    return created_jobs

def setup_candidates():
    """Create test candidates"""
    print("🔧 Setting up candidates...")
    
    # Get admin user for recruiter
    admin_user = User.objects.filter(email='admin@rslsolution.com').first()
    if not admin_user:
        print("❌ Admin user not found. Please run setup_admin_user first.")
        return []
    
    candidates_data = [
        {
            'full_name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-0001',
            'work_experience': 3,
            'domain': 'Technology',
            'status': 'NEW'
        },
        {
            'full_name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'phone': '+1-555-0002',
            'work_experience': 5,
            'domain': 'Technology',
            'status': 'NEW'
        },
        {
            'full_name': 'Dhananjay Paturkar',
            'email': 'dhananjay.paturkar@example.com',
            'phone': '+1-555-0003',
            'work_experience': 4,
            'domain': 'Technology',
            'status': 'NEW'
        }
    ]
    
    created_candidates = []
    for candidate_data in candidates_data:
        try:
            candidate, created = Candidate.objects.get_or_create(
                email=candidate_data['email'],
                defaults={
                    **candidate_data,
                    'recruiter': admin_user
                }
            )
            if created:
                print(f"✅ Created candidate: {candidate.full_name}")
            else:
                print(f"✅ Candidate already exists: {candidate.full_name}")
            created_candidates.append(candidate)
        except Exception as e:
            print(f"❌ Error creating candidate {candidate_data['full_name']}: {e}")
    
    return created_candidates

def run_migrations():
    """Run database migrations"""
    print("🔧 Running database migrations...")
    
    try:
        call_command('migrate', verbosity=1)
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Persistent Database for Render")
    print("=" * 50)
    print(f"📅 Setup time: {datetime.now()}")
    print()
    
    # Run setup steps
    steps = [
        ("Running migrations", run_migrations),
        ("Setting up admin user", setup_admin_user),
        ("Setting up test users", setup_test_users),
        ("Setting up domains", setup_domains),
        ("Setting up companies", setup_companies),
        ("Setting up jobs", setup_jobs),
        ("Setting up candidates", setup_candidates),
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        try:
            result = step_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r is not False)
    total = len(results)
    
    if passed == total:
        print("🎉 All setup steps completed successfully!")
        print("\n✅ Your database is now properly configured with:")
        print("   - Admin user (admin@rslsolution.com / admin123)")
        print("   - Test users for different roles")
        print("   - Sample companies and jobs")
        print("   - Test candidates")
        print("   - Default domains")
        
        print("\n💡 To verify persistence:")
        print("   1. Deploy your code to Render")
        print("   2. Check that data persists after deployment")
        print("   3. Use the admin credentials to log in")
        print("   4. Verify that all test data is still present")
        
    else:
        print(f"⚠️  {total - passed} out of {total} setup steps failed.")
        print("\n🔧 Recommended actions:")
        print("   1. Check Render logs for deployment errors")
        print("   2. Verify database connection in Render dashboard")
        print("   3. Run setup script again after fixing issues")
        print("   4. Contact Render support if problems persist")
    
    print("\n📝 Next steps:")
    print("   1. Commit and push these changes")
    print("   2. Deploy to Render")
    print("   3. Test login with admin credentials")
    print("   4. Verify data persistence across deployments")

if __name__ == '__main__':
    main()

