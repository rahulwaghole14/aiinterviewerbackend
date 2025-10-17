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
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

# No additional downloads needed - punkt_tab is not a valid NLTK resource


class ResumeJobMatcher:
    """
    Utility class for matching resume content with job descriptions
    """

    def __init__(self):
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()

        # Common technical skills and keywords
        self.technical_keywords = {
            "programming_languages": [
                "python",
                "java",
                "javascript",
                "typescript",
                "c++",
                "c#",
                "php",
                "ruby",
                "go",
                "rust",
                "swift",
                "kotlin",
                "scala",
                "r",
                "matlab",
                "sql",
                "html",
                "css",
                "bash",
                "powershell",
            ],
            "frameworks": [
                "django",
                "flask",
                "fastapi",
                "spring",
                "express",
                "react",
                "angular",
                "vue",
                "node.js",
                "laravel",
                "rails",
                "asp.net",
                "tensorflow",
                "pytorch",
                "scikit-learn",
                "pandas",
                "numpy",
            ],
            "databases": [
                "mysql",
                "postgresql",
                "mongodb",
                "redis",
                "elasticsearch",
                "oracle",
                "sqlite",
                "mariadb",
                "cassandra",
                "dynamodb",
                "firebase",
            ],
            "cloud_platforms": [
                "aws",
                "azure",
                "gcp",
                "heroku",
                "digitalocean",
                "linode",
                "vultr",
                "kubernetes",
                "docker",
            ],
            "tools": [
                "git",
                "jenkins",
                "jira",
                "confluence",
                "slack",
                "teams",
                "figma",
                "adobe",
                "postman",
                "swagger",
                "maven",
                "gradle",
                "npm",
                "yarn",
                "pip",
                "conda",
            ],
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
        text = text.translate(str.maketrans("", "", string.punctuation))

        # Simple tokenization without NLTK to avoid punkt_tab error
        tokens = text.split()

        # Remove stop words and lemmatize
        processed_tokens = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 2:
                lemmatized = self.lemmatizer.lemmatize(token)
                processed_tokens.append(lemmatized)

        return " ".join(processed_tokens)

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

    def calculate_skill_match(
        self, resume_skills: Dict[str, List[str]], job_skills: Dict[str, List[str]]
    ) -> float:
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

    def calculate_text_similarity(
        self, resume_text: str, job_description: str
    ) -> float:
        """
        Calculate text similarity using multiple advanced approaches for maximum accuracy
        """
        if not resume_text or not job_description:
            return 0.0

        processed_resume = self.preprocess_text(resume_text)
        processed_job = self.preprocess_text(job_description)

        if not processed_resume or not processed_job:
            return 0.0

        # Calculate multiple similarity scores
        word_similarity = self._calculate_word_similarity(
            processed_resume, processed_job
        )
        phrase_similarity = self._calculate_phrase_similarity(
            processed_resume, processed_job
        )
        semantic_similarity = self._calculate_semantic_similarity(
            processed_resume, processed_job
        )

        # Use sequence matcher for longer, similar-length texts
        resume_words = len(processed_resume.split())
        job_words = len(processed_job.split())

        sequence_score = 0
        if (
            resume_words >= 20
            and job_words >= 20
            and abs(resume_words - job_words) <= 50
        ):
            similarity = SequenceMatcher(None, processed_resume, processed_job).ratio()
            sequence_score = similarity * 100

        # Weighted combination of all approaches
        # Word similarity: 40%, Phrase similarity: 30%, Semantic: 20%, Sequence: 10%
        final_score = (
            word_similarity * 0.4
            + phrase_similarity * 0.3
            + semantic_similarity * 0.2
            + sequence_score * 0.1
        )

        # Additional boost for exact skill matches in job requirements
        job_lower = job_description.lower()
        resume_lower = resume_text.lower()

        # Check for exact skill mentions in job description
        skill_mentions = 0
        for category, skills in self.technical_keywords.items():
            for skill in skills:
                if skill in job_lower and skill in resume_lower:
                    skill_mentions += 1

        # Add bonus for exact skill matches (2% per match, max 20%)
        skill_bonus = min(20.0, skill_mentions * 2)

        # Final score with skill bonus
        final_score_with_bonus = min(100.0, final_score + skill_bonus)

        return final_score_with_bonus

    def _calculate_word_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity based on common words with enhanced matching
        """
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard_similarity = len(intersection) / len(union) if union else 0.0

        # Boost similarity for technical keywords
        all_technical_words = set(
            [word for category in self.technical_keywords.values() for word in category]
        )

        technical_words1 = words1.intersection(all_technical_words)
        technical_words2 = words2.intersection(all_technical_words)
        technical_intersection = technical_words1.intersection(technical_words2)

        # Enhanced technical boost based on category importance
        technical_boost = 0
        for category, keywords in self.technical_keywords.items():
            category_words1 = words1.intersection(set(keywords))
            category_words2 = words2.intersection(set(keywords))
            category_intersection = category_words1.intersection(category_words2)

            # Different boost weights for different categories
            if category == "programming_languages":
                technical_boost += (
                    len(category_intersection) * 0.15
                )  # 15% per programming language match
            elif category == "frameworks":
                technical_boost += (
                    len(category_intersection) * 0.12
                )  # 12% per framework match
            elif category == "databases":
                technical_boost += (
                    len(category_intersection) * 0.10
                )  # 10% per database match
            else:
                technical_boost += (
                    len(category_intersection) * 0.08
                )  # 8% per other technical word match

        # Additional boost for domain-specific terms
        domain_terms = [
            "data",
            "science",
            "machine",
            "learning",
            "analytics",
            "statistics",
            "python",
            "r",
            "sql",
        ]
        domain_words1 = words1.intersection(set(domain_terms))
        domain_words2 = words2.intersection(set(domain_terms))
        domain_intersection = domain_words1.intersection(domain_words2)
        domain_boost = len(domain_intersection) * 0.05  # 5% per domain term match

        final_similarity = min(
            100.0, (jaccard_similarity * 100) + technical_boost + domain_boost
        )
        return final_similarity

    def _calculate_phrase_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity based on common phrases and n-grams
        """
        words1 = text1.split()
        words2 = text2.split()

        if not words1 or not words2:
            return 0.0

        # Generate bigrams and trigrams
        def generate_ngrams(words, n):
            return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]

        bigrams1 = set(generate_ngrams(words1, 2))
        bigrams2 = set(generate_ngrams(words2, 2))
        trigrams1 = set(generate_ngrams(words1, 3))
        trigrams2 = set(generate_ngrams(words2, 3))

        # Calculate phrase overlaps
        bigram_overlap = (
            len(bigrams1.intersection(bigrams2)) / len(bigrams1.union(bigrams2))
            if bigrams1.union(bigrams2)
            else 0
        )
        trigram_overlap = (
            len(trigrams1.intersection(trigrams2)) / len(trigrams1.union(trigrams2))
            if trigrams1.union(trigrams2)
            else 0
        )

        # Weighted phrase similarity (bigrams more important than trigrams)
        phrase_similarity = (bigram_overlap * 0.7 + trigram_overlap * 0.3) * 100

        # Boost for technical phrases
        technical_phrases = [
            "machine learning",
            "data science",
            "deep learning",
            "artificial intelligence",
            "data analysis",
            "statistical analysis",
            "predictive modeling",
            "data visualization",
            "business intelligence",
            "data mining",
            "natural language processing",
            "computer vision",
            "neural networks",
            "big data",
            "cloud computing",
        ]

        tech_phrase_boost = 0
        for phrase in technical_phrases:
            if phrase in text1.lower() and phrase in text2.lower():
                tech_phrase_boost += 5  # 5% boost per technical phrase match

        return min(100.0, phrase_similarity + tech_phrase_boost)

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity based on concept and context matching
        """
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        # Define semantic groups (related concepts)
        semantic_groups = {
            "data_analysis": [
                "data",
                "analysis",
                "analytics",
                "insights",
                "patterns",
                "trends",
            ],
            "machine_learning": [
                "machine",
                "learning",
                "algorithm",
                "model",
                "prediction",
                "training",
            ],
            "programming": [
                "programming",
                "coding",
                "development",
                "software",
                "application",
            ],
            "statistics": [
                "statistics",
                "statistical",
                "probability",
                "distribution",
                "regression",
            ],
            "visualization": ["visualization", "chart", "graph", "dashboard", "report"],
            "database": ["database", "sql", "query", "storage", "retrieval"],
            "cloud": ["cloud", "aws", "azure", "gcp", "infrastructure", "deployment"],
            "business": [
                "business",
                "strategy",
                "management",
                "leadership",
                "stakeholder",
            ],
        }

        semantic_score = 0
        for group_name, concepts in semantic_groups.items():
            concepts1 = words1.intersection(set(concepts))
            concepts2 = words2.intersection(set(concepts))

            if concepts1 and concepts2:
                # Calculate overlap within this semantic group
                overlap = len(concepts1.intersection(concepts2))
                total_concepts = len(concepts1.union(concepts2))
                group_similarity = overlap / total_concepts if total_concepts > 0 else 0

                # Weight different groups differently
                if group_name in ["data_analysis", "machine_learning"]:
                    semantic_score += group_similarity * 15  # 15% per group
                elif group_name in ["programming", "statistics"]:
                    semantic_score += group_similarity * 12  # 12% per group
                else:
                    semantic_score += group_similarity * 8  # 8% per group

        return min(100.0, semantic_score)

    def calculate_experience_match(
        self, resume_experience: int, job_requirements: str
    ) -> float:
        """
        Calculate experience matching percentage
        """
        if not job_requirements or resume_experience is None:
            return 0.0

        # Extract experience requirements from job description
        experience_patterns = [
            r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience",
            r"experience:\s*(\d+)\+?\s*(?:years?|yrs?)",
            r"minimum\s*(\d+)\s*(?:years?|yrs?)\s*experience",
            r"(\d+)\+?\s*(?:years?|yrs?)\s*in\s*.*",
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

    def calculate_overall_match(
        self, resume_data: Dict, job_description: str
    ) -> Dict[str, float]:
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
        if not resume_data.get("parsed_text") or not job_description:
            return {
                "overall_match": 0.0,
                "skill_match": 0.0,
                "text_similarity": 0.0,
                "experience_match": 0.0,
            }

        # Extract skills from both resume and job description
        resume_skills = self.extract_skills_from_text(resume_data["parsed_text"])
        job_skills = self.extract_skills_from_text(job_description)

        # Calculate individual match scores
        skill_match = self.calculate_skill_match(resume_skills, job_skills)
        text_similarity = self.calculate_text_similarity(
            resume_data["parsed_text"], job_description
        )
        experience_match = self.calculate_experience_match(
            resume_data.get("work_experience", 0), job_description
        )

        # Calculate weighted overall match
        # Updated weights: Skills (35%), Text Similarity (40%), Experience (25%)
        # Text similarity is now more important due to improved algorithm
        overall_match = (
            (skill_match * 0.35) + (text_similarity * 0.40) + (experience_match * 0.25)
        )

        return {
            "overall_match": round(overall_match, 1),
            "skill_match": round(skill_match, 1),
            "text_similarity": round(text_similarity, 1),
            "experience_match": round(experience_match, 1),
            "resume_skills": resume_skills,
            "job_skills": job_skills,
        }


# Global instance for easy access
resume_matcher = ResumeJobMatcher()
