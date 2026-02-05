import re
import json
from typing import Dict, List, Tuple, Optional
import google.generativeai as genai
from django.conf import settings


class GeminiResumeMatcher:
    """
    Use Gemini AI to analyze resume-job matching and extract experience
    """

    def __init__(self):
        # Configure Gemini API
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            print("✅ Gemini Resume Matcher initialized successfully")
        else:
            print("❌ GEMINI_API_KEY not configured")
            self.model = None

    def extract_experience_from_resume(self, resume_text: str) -> Optional[int]:
        """
        Extract years of experience from resume using Gemini AI
        
        Args:
            resume_text: Full resume text
            
        Returns:
            Integer years of experience or None if not found
        """
        if not self.model or not resume_text:
            return None

        prompt = f"""
        Analyze the following resume text and extract the TOTAL years of work experience.
        
        Resume Text:
        {resume_text}
        
        Instructions:
        1. Look for phrases like "X years of experience", "X+ years", "X years experience"
        2. Consider all work experiences mentioned and calculate the total
        3. If multiple experiences are mentioned, sum them up (considering overlaps)
        4. Return ONLY a single integer number representing total years of experience
        5. If no clear experience information is found, return 0
        
        Examples:
        - "5 years of software development experience" -> 5
        - "3+ years in frontend, 2 years in backend" -> 5
        - "Experience from 2018 to 2023" -> 5
        - "No experience mentioned" -> 0
        
        Respond with Decimal number, no explanation:
        -if experience is only in months or less then 1 year then show the month infront of that month number)
        Examples:
        - "6 month of software development experience" -> 6 Months
        - "8 months in frontend" -> 8 Months
        """

        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                # Extract integer from response
                experience_match = re.search(r'\d+', response.text.strip())
                if experience_match:
                    return int(experience_match.group())
            return 0
        except Exception as e:
            print(f"❌ Error extracting experience with Gemini: {e}")
            # Fallback to regex extraction
            exp_re = re.compile(r"(\d{1,2})\s*(?:\+?\s*)?(?:years?|yrs?)", re.I)
            exp_match = exp_re.search(resume_text)
            if exp_match:
                return int(exp_match.group(1))
            return None

    def calculate_match_percentage(self, resume_text: str, job_description: str) -> Dict[str, float]:
        """
        Calculate match percentage between resume and job description using Gemini AI
        
        Args:
            resume_text: Full resume text
            job_description: Job description text
            
        Returns:
            Dictionary with match percentages
        """
        if not self.model or not resume_text or not job_description:
            return {
                "overall_match": 0.0,
                "skill_match": 0.0,
                "experience_match": 0.0,
                "education_match": 0.0,
                "relevance_score": 0.0
            }

        prompt = f"""
        Analyze the match between a candidate's resume and a job description.
        Provide detailed scoring for different aspects.
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME:
        {resume_text}
        
        Instructions:
        1. Analyze skills matching (technical skills, tools, technologies)
        2. Evaluate experience relevance and level
        3. Check education and qualifications alignment
        4. Assess overall relevance to the role
        
        Scoring Criteria:
        - Skill Match: How well the candidate's skills match job requirements (0-100)
        - Experience Match: How well the experience level matches requirements (0-100)
        - Education Match: How well education aligns with job needs (0-100)
        - Relevance Score: Overall relevance of resume to this specific role (0-100)
        - Overall Match: Weighted average of all factors (0-100)
        
        Weight the scores as follows for Overall Match:
        - Skill Match: 40%
        - Experience Match: 30%
        - Education Match: 15%
        - Relevance Score: 15%
        
        Respond in JSON format only:
        {{
            "skill_match": <score>,
            "experience_match": <score>,
            "education_match": <score>,
            "relevance_score": <score>,
            "overall_match": <score>
        }}
        
        Consider:
        - Direct skill matches are more valuable than related skills
        - Recent experience is more valuable than old experience
        - Specific achievements and projects add value
        - Industry-specific knowledge is beneficial
        """

        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)
                if json_match:
                    scores = json.loads(json_match.group())
                    # Ensure all required keys exist and are valid numbers
                    return {
                        "overall_match": float(scores.get("overall_match", 0)),
                        "skill_match": float(scores.get("skill_match", 0)),
                        "experience_match": float(scores.get("experience_match", 0)),
                        "education_match": float(scores.get("education_match", 0)),
                        "relevance_score": float(scores.get("relevance_score", 0))
                    }
            
            # Fallback if JSON parsing fails - use simple keyword matching
            return self._fallback_match_calculation(resume_text, job_description)
            
        except Exception as e:
            print(f"❌ Error calculating match with Gemini: {e}")
            # Return fallback calculation
            return self._fallback_match_calculation(resume_text, job_description)

    def analyze_resume_comprehensive(self, resume_text: str, job_description: str = None) -> Dict:
        """
        Comprehensive resume analysis using Gemini AI
        
        Args:
            resume_text: Full resume text
            job_description: Optional job description for context
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        if not self.model or not resume_text:
            return {}

        job_context = f"\n\nJOB CONTEXT:\n{job_description}" if job_description else ""
        
        prompt = f"""
        Perform a comprehensive analysis of the following resume{job_context}.
        
        RESUME TEXT:
        {resume_text}
        
        Provide analysis in the following JSON format:
        {{
            "extracted_info": {{
                "full_name": "<candidate's full name>",
                "email": "<email address>",
                "phone": "<phone number>",
                "total_experience_years": <integer>,
                "current_role": "<current/most recent role>",
                "key_skills": ["<skill1>", "<skill2>", "..."],
                "education": ["<education1>", "<education2>", "..."],
                "certifications": ["<cert1>", "<cert2>", "..."]
            }},
            "analysis": {{
                "career_level": "<Junior|Mid|Senior|Lead|Manager>",
                "industry_focus": "<primary industry/domain>",
                "strengths": ["<strength1>", "<strength2>", "..."],
                "areas_for_improvement": ["<area1>", "<area2>", "..."]
            }}
        }}
        
        Instructions:
        1. Extract all available information accurately
        2. Infer career level from experience and responsibilities
        3. Identify key technical and soft skills
        4. Highlight strengths and areas that could be improved
        5. Respond with valid JSON only
        """

        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
            
            return {}
            
        except Exception as e:
            print(f"❌ Error in comprehensive resume analysis: {e}")
            return {}

    def _fallback_match_calculation(self, resume_text: str, job_description: str) -> Dict[str, float]:
        """
        Fallback match calculation using keyword matching when Gemini API is unavailable
        """
        if not resume_text or not job_description:
            return {
                "overall_match": 0.0,
                "skill_match": 0.0,
                "experience_match": 0.0,
                "education_match": 0.0,
                "relevance_score": 0.0
            }
        
        # Simple keyword matching for fallback
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()
        
        # Common technical skills
        technical_skills = ['python', 'java', 'javascript', 'react', 'django', 'flask', 'nodejs', 'sql', 'mongodb', 'postgresql', 'aws', 'docker', 'git']
        
        # Calculate skill match
        found_skills = sum(1 for skill in technical_skills if skill in resume_lower)
        total_skills = len([skill for skill in technical_skills if skill in jd_lower])
        skill_match = (found_skills / max(total_skills, 1)) * 100 if total_skills > 0 else 0
        
        # Experience matching (simple year extraction)
        exp_re = re.compile(r'(\d+)\s*(?:\+?\s*)?(?:years?|yrs?)', re.I)
        resume_exp = exp_re.search(resume_lower)
        jd_exp = exp_re.search(jd_lower)
        
        resume_years = int(resume_exp.group(1)) if resume_exp else 0
        jd_years = int(jd_exp.group(1)) if jd_exp else 0
        
        experience_match = min(resume_years / max(jd_years, 1) * 100, 100) if jd_years > 0 else 50
        
        # Education match (simple keyword matching)
        education_keywords = ['bachelor', 'master', 'degree', 'university', 'college']
        education_match = 80.0 if any(keyword in resume_lower for keyword in education_keywords) else 40.0
        
        # Overall match (weighted average)
        overall_match = (skill_match * 0.4 + experience_match * 0.3 + education_match * 0.15 + 50.0 * 0.15)
        
        return {
            "overall_match": round(overall_match, 1),
            "skill_match": round(skill_match, 1),
            "experience_match": round(experience_match, 1),
            "education_match": round(education_match, 1),
            "relevance_score": round((skill_match + experience_match) / 2, 1)
        }


# Global instance for easy access
gemini_resume_matcher = GeminiResumeMatcher()
