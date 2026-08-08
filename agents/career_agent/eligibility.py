# agents/career_agent/eligibility.py

import re

# 1. Each role has skills with a weight (importance points)
ROLES = {
    "Data Scientist": {
        "Python": 25, "Machine Learning": 25, "Statistics": 20,
        "SQL": 12, "Pandas": 10, "Data Visualization": 8,
    },
    "Data Engineer": {
        "Python": 20, "SQL": 20, "ETL": 18,
        "Data Warehousing": 15, "Spark": 15, "Cloud": 12,
    },
    "Data Analyst": {
        "SQL": 25, "Excel": 20, "Power BI": 20,
        "Statistics": 20, "Data Visualization": 15,
    },
    "ML Engineer": {
        "Python": 22, "Machine Learning": 20, "Deep Learning": 18,
        "MLOps": 15, "Docker": 13, "API Development": 12,
    },
    "Software Engineer": {
        "Data Structures": 20, "Algorithms": 20, "OOP": 18,
        "SQL": 15, "Git": 12, "REST APIs": 15,
    },
}

THRESHOLD = 80   # need 80% to be eligible

# map common abbreviations -> canonical skill name (lowercase)
SYNONYMS = {
    "ml": "machine learning",
    "dl": "deep learning",
    "sklearn": "scikit-learn",
    "aws": "cloud", "gcp": "cloud", "azure": "cloud",
    "js": "javascript",
    "data viz": "data visualization",
    "powerbi": "power bi",
    "dsa": "data structures",
    "basic dsa": "data structures",
    "oops": "oop",
    "stats": "statistics",
    "ms excel": "excel",
}
REQUIRED_FIELDS = {
    "tenth_percentage": "your 10th grade percentage",
    "twelfth_percentage": "your 12th grade percentage",
    "degree": "your degree (e.g. B.Tech)",
    "branch": "your branch/specialization",
    "cgpa": "your current CGPA",
    "skills": "your key skills",
}

def find_missing_fields(profile: dict):
    missing = {}
    for field, question_text in REQUIRED_FIELDS.items():
        value = profile.get(field)
        if value is None or value == "" or value == []:
            missing[field] = question_text
    return missing

def _canon(skill: str) -> str:
    """Normalize a skill and map known abbreviations to the full name."""
    s = skill.strip().lower()
    return SYNONYMS.get(s, s)


def _extract_cgpa_cutoff(context: str):
    """Find a required CGPA like '7.0', '6.5 CGPA' in RAG text."""
    if not context:
        return None
    matches = re.findall(r"(\d(?:\.\d+)?)\s*(?:\+|cgpa|gpa)?", context.lower())
    cgpas = [float(m) for m in matches if 0 < float(m) <= 10]
    return max(cgpas) if cgpas else None


def score_eligibility(role, user_skills):
    role = role.strip().title()          # "data analyst" -> "Data Analyst"

    # allow "Microsoft Data Analyst" -> "Data Analyst"
    for known in ROLES:
        if known.lower() in role.lower():
            role = known
            break

    if role not in ROLES:
        return {"error": f"Unknown role: {role}",
                "score": 0, "eligible": False, "suggestions": []}

    weights = ROLES[role]                # skills + weights for this role
    total = sum(weights.values())        # total points for this role

    user = {_canon(s) for s in user_skills}   # canonicalize user skills

    earned = 0
    missing = []

    # 2. go through each required skill
    for skill, weight in weights.items():
        if _canon(skill) in user:
            earned += weight             # user has it -> add points
        else:
            missing.append(skill)        # user is missing it

    # 3. calculate percentage
    score = round(earned / total * 100, 1)

    # 4. decide eligible or not
    eligible = score >= THRESHOLD

    return {
        "role": role,
        "score": score,
        "eligible": eligible,
        "suggestions": missing,          # key name matches agent.py
    }
