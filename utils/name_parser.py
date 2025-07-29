from nameparser import HumanName

UNWANTED_KEYWORDS = {
    "Data", "Engineer", "Developer", "Scientist", "Analyst", "Intern", "Manager", "Student",
    "Professional", "Lead", "Consultant", "Technician", "Specialist", "Architect", "Associate",
    "Executive", "Fresher", "Trainer", "Expert", "Staff", "Head", "Coordinator", "Support",
    "Freelancer", "Operator", "Assistant", "Trainee", "CEO", "CTO", "COO", "Director", "VP",
    "Principal", "President", "Founder", "Owner", "Self-employed", "SDE", "HR", "Recruiter",
    "Supervisor", "Controller", "Officer", "Apprentice", "Programmer", "Software", "Hardware",
    "Admin", "Automation", "AI", "ML", "Python", "Java", "Fullstack", "Frontend", "Backend",
    "System", "Network", "Cybersecurity", "Testing", "QA", "DevOps", "R&D", "Embedded"
}

def parse_candidate_name(raw_name: str) -> str:
    name = HumanName(raw_name)
    unwanted = {kw.lower() for kw in UNWANTED_KEYWORDS}

    parts = []
    if name.first and name.first.strip().lower() not in unwanted:
        parts.append(name.first.strip())

    if name.middle and name.middle.strip().lower() not in unwanted:
        parts.append(name.middle.strip())

    if name.last and name.last.strip().lower() not in unwanted:
        parts.append(name.last.strip())

    return " ".join(parts)
