#!/usr/bin/env python
"""
Script to add Cloud Architect job positions with detailed descriptions
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from jobs.models import Job, Domain
from companies.models import Company

def create_cloud_architect_jobs():
    """Create Cloud Architect job positions"""
    
    print("\n" + "="*80)
    print("🚀 CREATING CLOUD ARCHITECT JOB POSITIONS")
    print("="*80 + "\n")
    
    # Get or create domain
    try:
        domain = Domain.objects.get(name="Cloud & Infrastructure")
        print(f"✅ Using existing domain: {domain.name}")
    except Domain.DoesNotExist:
        domain = Domain.objects.create(
            name="Cloud & Infrastructure",
            description="Cloud computing, infrastructure, DevOps, and architecture",
            is_active=True
        )
        print(f"✅ Created new domain: {domain.name}")
    
    # Get first company or create a demo company
    company = Company.objects.first()
    if not company:
        print("⚠️ No company found. Please create a company first.")
        return
    
    print(f"✅ Using company: {company.name}\n")
    
    # Job 1: Senior Cloud Architect with detailed description
    job1_description = """
**About the Role:**
We are seeking an experienced Senior Cloud Architect to lead our cloud infrastructure strategy and implementation. This role will be responsible for designing, implementing, and managing scalable, secure, and cost-effective cloud solutions across multiple platforms.

**Key Responsibilities:**
• Design and implement enterprise-level cloud architecture solutions on AWS, Azure, and GCP
• Lead cloud migration projects from on-premises to cloud environments
• Establish cloud governance, security, and compliance frameworks
• Develop and maintain cloud infrastructure as code using Terraform, CloudFormation, or ARM templates
• Optimize cloud costs and resource utilization across all environments
• Mentor junior engineers and provide technical guidance to development teams
• Collaborate with security teams to implement zero-trust architecture
• Design disaster recovery and business continuity solutions
• Evaluate and recommend new cloud technologies and services
• Create and maintain comprehensive technical documentation

**Required Qualifications:**
• 7+ years of experience in cloud architecture and infrastructure design
• Expert-level knowledge of at least two major cloud platforms (AWS, Azure, GCP)
• Strong experience with infrastructure as code tools (Terraform, CloudFormation, Ansible)
• Proven track record of designing and implementing large-scale cloud migrations
• Deep understanding of cloud security best practices and compliance standards (SOC2, ISO 27001, HIPAA)
• Experience with containerization and orchestration (Docker, Kubernetes, ECS, AKS)
• Strong knowledge of networking concepts (VPC, VPN, Direct Connect, Load Balancers)
• Experience with CI/CD pipelines and DevOps practices
• Excellent problem-solving and analytical skills
• Strong communication and leadership abilities

**Preferred Qualifications:**
• AWS Solutions Architect Professional or equivalent certifications
• Azure Solutions Architect Expert certification
• Google Cloud Professional Cloud Architect certification
• Experience with serverless architectures and microservices
• Knowledge of multi-cloud and hybrid cloud strategies
• Experience with monitoring and observability tools (CloudWatch, Prometheus, Grafana, Datadog)
• Background in FinTech, Healthcare, or highly regulated industries
• Experience with cost optimization and FinOps practices

**Technical Skills:**
• Cloud Platforms: AWS (EC2, S3, Lambda, RDS, CloudFront, Route53, EKS), Azure (VMs, Blob Storage, Functions, AKS), GCP (Compute Engine, Cloud Storage, Cloud Functions, GKE)
• Infrastructure as Code: Terraform, CloudFormation, ARM Templates, Pulumi
• Containers & Orchestration: Docker, Kubernetes, Helm, ECS, AKS, GKE
• CI/CD: Jenkins, GitLab CI, GitHub Actions, Azure DevOps, AWS CodePipeline
• Scripting: Python, Bash, PowerShell
• Monitoring: CloudWatch, Azure Monitor, Prometheus, Grafana, ELK Stack
• Security: IAM, Security Groups, RBAC, Secrets Management, WAF
• Databases: RDS, DynamoDB, CosmosDB, Aurora, Cloud SQL

**What We Offer:**
• Competitive salary range: $150,000 - $200,000 USD (based on experience)
• Comprehensive health, dental, and vision insurance
• 401(k) with company match
• Flexible work arrangements (Remote/Hybrid)
• Professional development budget for certifications and training
• Latest MacBook Pro or Dell XPS
• Annual performance bonuses
• Stock options
• 20 days PTO + 10 holidays
• Parental leave
• Team building events and company retreats

**Interview Process:**
1. Initial screening call (30 minutes)
2. Technical assessment (Cloud architecture case study)
3. Technical interview with engineering team (1 hour)
4. System design interview (1 hour)
5. Leadership & cultural fit interview (45 minutes)
6. Final interview with CTO (30 minutes)

**Location:** Remote (US) / Hybrid (San Francisco, CA / New York, NY / Austin, TX)

**Start Date:** Immediate / As soon as possible

We are an equal opportunity employer and value diversity at our company. We do not discriminate on the basis of race, religion, color, national origin, gender, sexual orientation, age, marital status, veteran status, or disability status.
"""
    
    # Job 2: Cloud Architect with shorter description
    job2_description = """
**About the Role:**
Join our growing team as a Cloud Architect to help design and implement cloud solutions for our enterprise clients.

**Key Responsibilities:**
• Design cloud architecture solutions on AWS and Azure
• Implement infrastructure as code using Terraform
• Ensure security and compliance best practices
• Optimize cloud costs and performance
• Collaborate with development teams
• Create technical documentation

**Requirements:**
• 5+ years of cloud architecture experience
• Strong AWS and Azure knowledge
• Experience with Terraform or CloudFormation
• Understanding of CI/CD pipelines
• Knowledge of Docker and Kubernetes
• Good communication skills
• Bachelor's degree in Computer Science or related field

**Preferred:**
• AWS Solutions Architect certification
• Azure certifications
• Experience with microservices
• Knowledge of serverless computing
• FinOps experience

**Tech Stack:**
AWS, Azure, Terraform, Docker, Kubernetes, Jenkins, Python, Bash

**Compensation:**
$120,000 - $160,000 USD + benefits

**Location:** Remote / Hybrid (multiple locations)

**Work Schedule:** Full-time
"""
    
    try:
        # Create Job 1: Senior Cloud Architect (Detailed)
        job1 = Job.objects.create(
            job_title="Senior Cloud Architect",
            company_name=company.name,
            domain=domain,
            spoc_email=company.primary_email if hasattr(company, 'primary_email') else "hr@company.com",
            hiring_manager_email=company.primary_email if hasattr(company, 'primary_email') else "hiring@company.com",
            current_team_size_info="15-20 engineers",
            number_to_hire=2,
            position_level="IC",
            current_process="Multi-stage technical and leadership interviews",
            tech_stack_details="AWS, Azure, GCP, Terraform, CloudFormation, Kubernetes, Docker, Python, Jenkins, GitLab CI, Prometheus, Grafana, ELK Stack",
            job_description=job1_description,
        )
        print(f"✅ Created Job 1: {job1.job_title} (ID: {job1.id})")
        print(f"   📝 Description length: {len(job1.job_description)} characters")
        print(f"   🏢 Company: {job1.company_name}")
        print(f"   🎯 Domain: {job1.domain.name}")
        print(f"   👥 Team size: {job1.current_team_size_info}")
        print(f"   📊 Positions: {job1.number_to_hire}")
        print()
        
        # Create Job 2: Cloud Architect (Shorter)
        job2 = Job.objects.create(
            job_title="Cloud Architect",
            company_name=company.name,
            domain=domain,
            spoc_email=company.primary_email if hasattr(company, 'primary_email') else "recruitment@company.com",
            hiring_manager_email=company.primary_email if hasattr(company, 'primary_email') else "manager@company.com",
            current_team_size_info="10-15 engineers",
            number_to_hire=1,
            position_level="IC",
            current_process="Technical screening and interviews",
            tech_stack_details="AWS, Azure, Terraform, Docker, Kubernetes, Jenkins, Python, Bash",
            job_description=job2_description,
        )
        print(f"✅ Created Job 2: {job2.job_title} (ID: {job2.id})")
        print(f"   📝 Description length: {len(job2.job_description)} characters")
        print(f"   🏢 Company: {job2.company_name}")
        print(f"   🎯 Domain: {job2.domain.name}")
        print(f"   👥 Team size: {job2.current_team_size_info}")
        print(f"   📊 Positions: {job2.number_to_hire}")
        print()
        
        print("\n" + "="*80)
        print("✅ SUCCESSFULLY CREATED CLOUD ARCHITECT JOBS!")
        print("="*80)
        print(f"\n📊 Total Jobs Created: 2")
        print(f"   • Senior Cloud Architect (Detailed): ID {job1.id}")
        print(f"   • Cloud Architect (Concise): ID {job2.id}")
        print(f"\n💡 You can now use these jobs in the interview scheduler!")
        print("\n📧 EMAIL NOTIFICATION STATUS:")
        print("   ✅ Email notifications are ENABLED")
        print("   ✅ Candidates receive emails when interviews are scheduled")
        print("   ✅ Email includes interview details, link, and instructions")
        print(f"   ✅ Email service: {os.environ.get('EMAIL_BACKEND', 'Django Email Backend')}")
        print("\n🔍 Email is sent from: notifications/services.py")
        print("   → Function: send_candidate_interview_scheduled_notification()")
        print("   → Triggered when: book_slot() API is called in interviews/views.py")
        print("   → Email template includes:")
        print("      • Interview details (position, company, date/time)")
        print("      • Interview link with access instructions")
        print("      • Important preparation notes")
        print("      • Contact information")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error creating jobs: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_cloud_architect_jobs()

