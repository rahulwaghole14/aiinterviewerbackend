#!/usr/bin/env python3
"""
Script to add domains to the database for testing
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from jobs.models import Domain

def create_domains():
    """Create default domains for testing"""
    domains_data = [
        {
            'name': 'Software Development',
            'description': 'General software development and programming'
        },
        {
            'name': 'Python Development',
            'description': 'Python programming and development'
        },
        {
            'name': 'React Frontend',
            'description': 'React.js frontend development'
        },
        {
            'name': 'Data Science',
            'description': 'Data science and analytics'
        },
        {
            'name': 'DevOps',
            'description': 'DevOps and infrastructure'
        },
        {
            'name': 'Mobile Development',
            'description': 'Mobile app development'
        },
        {
            'name': 'Machine Learning',
            'description': 'Machine learning and AI'
        },
        {
            'name': 'Full Stack Development',
            'description': 'Full stack web development'
        }
    ]
    
    created_domains = []
    for domain_data in domains_data:
        domain, created = Domain.objects.get_or_create(
            name=domain_data['name'],
            defaults=domain_data
        )
        if created:
            print(f"✅ Created domain: {domain.name}")
            created_domains.append(domain)
        else:
            print(f"ℹ️  Domain already exists: {domain.name}")
    
    print(f"\n📊 Total domains available: {Domain.objects.filter(is_active=True).count()}")
    print("\nAvailable domains for job creation:")
    for domain in Domain.objects.filter(is_active=True):
        print(f"  - ID: {domain.id}, Name: {domain.name}")
    
    return created_domains

if __name__ == "__main__":
    print("🏗️  Setting up domains for testing...")
    create_domains()
    print("✅ Domain setup complete!") 