"""
Django management command to sync company names from Jobs to Company model
"""
from django.core.management.base import BaseCommand
from jobs.models import Job
from companies.models import Company


class Command(BaseCommand):
    help = 'Sync company names from Jobs to Company model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('🔄 Syncing companies from jobs...'))
        
        # Get all unique company names from jobs
        job_company_names = Job.objects.values_list('company_name', flat=True).distinct()
        existing_companies = set(Company.objects.values_list('name', flat=True))
        
        created_count = 0
        updated_count = 0
        
        for company_name in job_company_names:
            if not company_name or not company_name.strip():
                continue
                
            company_name = company_name.strip()
            
            if company_name not in existing_companies:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'  Would create: {company_name}')
                    )
                else:
                    Company.objects.get_or_create(
                        name=company_name,
                        defaults={
                            'description': f'Company created automatically from job postings',
                            'is_active': True,
                        }
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Created: {company_name}')
                    )
                    created_count += 1
            else:
                # Update existing company to ensure it's active
                if not dry_run:
                    company = Company.objects.get(name=company_name)
                    if not company.is_active:
                        company.is_active = True
                        company.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✅ Activated: {company_name}')
                        )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\n📊 Would create {len([n for n in job_company_names if n and n.strip() and n.strip() not in existing_companies])} companies')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Sync complete!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  Created: {created_count} companies')
            )
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  Activated: {updated_count} companies')
                )

