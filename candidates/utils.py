"""
Utility functions for candidate management
"""
from django.db.models import Q
from .models import Candidate
from jobs.models import Job


def check_candidate_duplicate(email, job_role=None, domain=None, recruiter=None):
    """
    Check if a candidate with the same email already exists for the same job role.
    
    Args:
        email (str): Candidate email address
        job_role (str, optional): Job role/title to check against
        domain (str, optional): Domain to check against
        recruiter (User, optional): Recruiter to check against (for data isolation)
    
    Returns:
        dict: Contains duplicate information if found, None otherwise
        {
            'is_duplicate': bool,
            'existing_candidate': Candidate object or None,
            'duplicate_reason': str,
            'job_title': str or None,
            'company_name': str or None
        }
    """
    if not email:
        return None
    
    # Build query to find existing candidates with the same email
    query = Q(email__iexact=email)
    
    # Add recruiter filter for data isolation if provided
    if recruiter:
        query &= Q(recruiter=recruiter)
    
    # Find candidates with the same email
    existing_candidates = Candidate.objects.filter(query)
    
    if not existing_candidates.exists():
        return {
            'is_duplicate': False,
            'existing_candidate': None,
            'duplicate_reason': None,
            'job_title': None,
            'company_name': None
        }
    
    # Priority 1: Check for exact job role match
    if job_role:
        for candidate in existing_candidates:
            if candidate.job and candidate.job.job_title.lower() == job_role.lower():
                return {
                    'is_duplicate': True,
                    'existing_candidate': candidate,
                    'duplicate_reason': f"Candidate with email '{email}' already exists for job role '{job_role}'",
                    'job_title': candidate.job.job_title,
                    'company_name': candidate.job.company_name
                }
    
    # Priority 2: Check for domain match only if no job role was provided
    # This prevents domain-based duplicates when we're checking for a specific job role
    if domain and not job_role:
        for candidate in existing_candidates:
            if candidate.domain and candidate.domain.lower() == domain.lower():
                return {
                    'is_duplicate': True,
                    'existing_candidate': candidate,
                    'duplicate_reason': f"Candidate with email '{email}' already exists in domain '{domain}'",
                    'job_title': candidate.job.job_title if candidate.job else None,
                    'company_name': candidate.job.company_name if candidate.job else None
                }
    
    # If no specific job/domain match, don't consider it a duplicate
    # This allows the same email to be used for different job roles/domains
    return {
        'is_duplicate': False,
        'existing_candidate': None,
        'duplicate_reason': None,
        'job_title': None,
        'company_name': None
    }


def get_duplicate_candidates_info(email, job_role=None, domain=None, recruiter=None):
    """
    Get detailed information about duplicate candidates.
    
    Args:
        email (str): Candidate email address
        job_role (str, optional): Job role/title to check against
        domain (str, optional): Domain to check against
        recruiter (User, optional): Recruiter to check against
    
    Returns:
        dict: Detailed duplicate information
    """
    duplicate_info = check_candidate_duplicate(email, job_role, domain, recruiter)
    
    if not duplicate_info or not duplicate_info['is_duplicate']:
        return duplicate_info
    
    existing_candidate = duplicate_info['existing_candidate']
    
    # Add more detailed information
    duplicate_info.update({
        'candidate_id': existing_candidate.id,
        'candidate_name': existing_candidate.full_name,
        'candidate_status': existing_candidate.status,
        'candidate_created_at': existing_candidate.created_at,
        'candidate_last_updated': existing_candidate.last_updated,
        'candidate_domain': existing_candidate.domain,
        'candidate_experience': existing_candidate.work_experience,
        'candidate_phone': existing_candidate.phone,
        'resume_url': existing_candidate.resume.file.url if existing_candidate.resume else None,
    })
    
    return duplicate_info


def format_duplicate_message(duplicate_info):
    """
    Format a user-friendly duplicate message.
    
    Args:
        duplicate_info (dict): Duplicate information from check_candidate_duplicate
    
    Returns:
        str: Formatted message
    """
    if not duplicate_info or not duplicate_info['is_duplicate']:
        return None
    
    reason = duplicate_info['duplicate_reason']
    candidate_name = duplicate_info.get('candidate_name', 'Unknown')
    job_title = duplicate_info.get('job_title', 'Unknown role')
    company_name = duplicate_info.get('company_name', 'Unknown company')
    status = duplicate_info.get('candidate_status', 'Unknown status')
    
    message = f"DUPLICATE: {reason}\n"
    message += f"Existing candidate: {candidate_name}\n"
    message += f"Job: {job_title}"
    
    if company_name and company_name != 'Unknown company':
        message += f" at {company_name}"
    
    message += f"\nStatus: {status}"
    
    return message
