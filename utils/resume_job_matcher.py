import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# No additional downloads needed - punkt_tab is not a valid NLTK resource

class ResumeJobMatcher:
    """
    Utility class for matching resume content with job descriptions
    """
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Common technical skills and keywords
        self.technical_keywords = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
                'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'bash', 'powershell'
            ],
            'frameworks': [
                'django', 'flask', 'fastapi', 'spring', 'express', 'react', 'angular', 'vue', 'node.js',
                'laravel', 'rails', 'asp.net', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sqlite', 'mariadb',
                'cassandra', 'dynamodb', 'firebase'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'heroku', 'digitalocean', 'linode', 'vultr', 'kubernetes', 'docker'
            ],
            'tools': [
                'git', 'jenkins', 'jira', 'confluence', 'slack', 'teams', 'figma', 'adobe', 'postman',
                'swagger', 'maven', 'gradle', 'npm', 'yarn', 'pip', 'conda'
            ]
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by removing punctuation, converting to lowercase, and lemmatizing
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Simple tokenization without NLTK to avoid punkt_tab error
        tokens = text.split()
        
        # Remove stop words and lemmatize
        processed_tokens = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 2:
                lemmatized = self.lemmatizer.lemmatize(token)
                processed_tokens.append(lemmatized)
        
        return ' '.join(processed_tokens)
    
    def extract_skills_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Extract technical skills from text
        """
        if not text:
            return {}
        
        text_lower = text.lower()
        extracted_skills = {}
        
        for category, keywords in self.technical_keywords.items():
            found_skills = []
            for keyword in keywords:
                if keyword in text_lower:
                    found_skills.append(keyword)
            if found_skills:
                extracted_skills[category] = found_skills
        
        return extracted_skills
    
    def calculate_skill_match(self, resume_skills: Dict[str, List[str]], job_skills: Dict[str, List[str]]) -> float:
        """
        Calculate skill matching percentage
        """
        if not job_skills:
            return 0.0
        
        total_job_skills = sum(len(skills) for skills in job_skills.values())
        if total_job_skills == 0:
            return 0.0
        
        matched_skills = 0
        for category, job_category_skills in job_skills.items():
            resume_category_skills = resume_skills.get(category, [])
            for skill in job_category_skills:
                if skill in resume_category_skills:
                    matched_skills += 1
        
        return (matched_skills / total_job_skills) * 100
    
    def calculate_text_similarity(self, resume_text: str, job_description: str) -> float:
        """
        Calculate text similarity using sequence matcher
        """
        if not resume_text or not job_description:
            return 0.0
        
        processed_resume = self.preprocess_text(resume_text)
        processed_job = self.preprocess_text(job_description)
        
        if not processed_resume or not processed_job:
            return 0.0
        
        similarity = SequenceMatcher(None, processed_resume, processed_job).ratio()
        return similarity * 100
    
    def calculate_experience_match(self, resume_experience: int, job_requirements: str) -> float:
        """
        Calculate experience matching percentage
        """
        if not job_requirements or resume_experience is None:
            return 0.0
        
        # Extract experience requirements from job description
        experience_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
            r'experience:\s*(\d+)\+?\s*(?:years?|yrs?)',
            r'minimum\s*(\d+)\s*(?:years?|yrs?)\s*experience',
            r'(\d+)\+?\s*(?:years?|yrs?)\s*in\s*.*'
        ]
        
        required_experience = None
        for pattern in experience_patterns:
            match = re.search(pattern, job_requirements, re.IGNORECASE)
            if match:
                required_experience = int(match.group(1))
                break
        
        if required_experience is None:
            return 50.0  # Default 50% if no experience requirement found
        
        if resume_experience >= required_experience:
            return 100.0
        elif resume_experience >= required_experience * 0.7:
            return 80.0
        elif resume_experience >= required_experience * 0.5:
            return 60.0
        else:
            return max(20.0, (resume_experience / required_experience) * 100)
    
    def calculate_overall_match(self, resume_data: Dict, job_description: str) -> Dict[str, float]:
        """
        Calculate overall matching percentage between resume and job description
        
        Args:
            resume_data: Dictionary containing resume information
                - parsed_text: Full resume text
                - work_experience: Years of experience
                - name: Candidate name
                - email: Candidate email
                - phone: Candidate phone
            job_description: Job description text
        
        Returns:
            Dictionary with matching percentages for different aspects
        """
        if not resume_data.get('parsed_text') or not job_description:
            return {
                'overall_match': 0.0,
                'skill_match': 0.0,
                'text_similarity': 0.0,
                'experience_match': 0.0
            }
        
        # Extract skills from both resume and job description
        resume_skills = self.extract_skills_from_text(resume_data['parsed_text'])
        job_skills = self.extract_skills_from_text(job_description)
        
        # Calculate individual match scores
        skill_match = self.calculate_skill_match(resume_skills, job_skills)
        text_similarity = self.calculate_text_similarity(resume_data['parsed_text'], job_description)
        experience_match = self.calculate_experience_match(
            resume_data.get('work_experience', 0), 
            job_description
        )
        
        # Calculate weighted overall match
        # Weights: Skills (40%), Text Similarity (35%), Experience (25%)
        overall_match = (skill_match * 0.4) + (text_similarity * 0.35) + (experience_match * 0.25)
        
        return {
            'overall_match': round(overall_match, 1),
            'skill_match': round(skill_match, 1),
            'text_similarity': round(text_similarity, 1),
            'experience_match': round(experience_match, 1),
            'resume_skills': resume_skills,
            'job_skills': job_skills
        }

# Global instance for easy access
resume_matcher = ResumeJobMatcher()
