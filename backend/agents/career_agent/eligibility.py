# backend/agents/career_agent/eligibility.py

import re
from typing import List, Dict, Optional

from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np


# ============================================================
# EMBEDDINGS
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_skill(skill: str) -> str:
    """
    Normalize a skill for easier comparison.
    """

    if not skill:
        return ""

    skill = skill.lower().strip()

    replacements = {
        "ml": "machine learning",
        "dl": "deep learning",
        "m.l.": "machine learning",
        "d.l.": "deep learning",
        "powerbi": "power bi",
        "power-bi": "power bi",
        "data viz": "data visualization",
        "stats": "statistics",
        "sklearn": "scikit learn",
        "scikit-learn": "scikit learn",
        "ms excel": "excel",
        "excel spreadsheet": "excel",
        "aws": "cloud",
        "azure": "cloud",
        "gcp": "cloud",
    }

    return replacements.get(skill, skill)


# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

def semantic_similarity(skill1: str, skill2: str) -> float:

    v1 = embeddings.embed_query(skill1)
    v2 = embeddings.embed_query(skill2)

    denominator = (
        np.linalg.norm(v1) *
        np.linalg.norm(v2)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(v1, v2) / denominator
    )


# ============================================================
# SEMANTIC SKILL MATCH
# ============================================================

def skills_match(
    student_skill: str,
    required_skill: str,
    threshold: float = 0.72
) -> bool:

    student = normalize_skill(student_skill)
    required = normalize_skill(required_skill)

    if not student or not required:
        return False

    # Exact match first
    if student == required:
        return True

    # Simple substring match
    if student in required or required in student:
        return True

    # Semantic match
    similarity = semantic_similarity(
        student,
        required
    )

    return similarity >= threshold


# ============================================================
# MATCH ALL SKILLS
# ============================================================

def evaluate_skills(
    student_skills: List[str],
    required_skills: List[str]
) -> Dict:

    matched = []
    missing = []

    for required in required_skills:

        found = False

        for student in student_skills:

            if skills_match(
                student,
                required
            ):
                found = True
                break

        if found:
            matched.append(required)
        else:
            missing.append(required)

    return {
        "matched_skills": matched,
        "missing_skills": missing
    }


# ============================================================
# ACADEMIC EVALUATION
# ============================================================

def evaluate_academics(
    cgpa: Optional[float],
    tenth: Optional[float],
    twelfth: Optional[float],
    requirements: Dict
) -> Dict:

    failures = []

    minimum_cgpa = requirements.get(
        "minimum_cgpa"
    )

    minimum_tenth = requirements.get(
        "minimum_10th"
    )

    minimum_twelfth = requirements.get(
        "minimum_12th"
    )

    # ------------------------------------------
    # CGPA
    # ------------------------------------------

    if (
        minimum_cgpa is not None
        and cgpa is not None
        and cgpa < float(minimum_cgpa)
    ):
        failures.append(
            f"CGPA must be at least {minimum_cgpa}"
        )

    # ------------------------------------------
    # 10th
    # ------------------------------------------

    if (
        minimum_tenth is not None
        and tenth is not None
        and tenth < float(minimum_tenth)
    ):
        failures.append(
            f"10th percentage must be at least "
            f"{minimum_tenth}%"
        )

    # ------------------------------------------
    # 12th
    # ------------------------------------------

    if (
        minimum_twelfth is not None
        and twelfth is not None
        and twelfth < float(minimum_twelfth)
    ):
        failures.append(
            f"12th percentage must be at least "
            f"{minimum_twelfth}%"
        )

    return {
        "academic_eligible":
            len(failures) == 0,

        "academic_failures":
            failures
    }


# ============================================================
# FINAL EVALUATION
# ============================================================

def evaluate_candidate(
    student_skills: List[str],
    required_skills: List[str],
    cgpa: Optional[float],
    tenth: Optional[float],
    twelfth: Optional[float],
    academic_requirements: Dict
) -> Dict:

    skill_result = evaluate_skills(
        student_skills,
        required_skills
    )

    academic_result = evaluate_academics(
        cgpa,
        tenth,
        twelfth,
        academic_requirements
    )

    # --------------------------------------------------------
    # Eligibility
    #
    # No score.
    #
    # Student is eligible only when:
    # 1. Academic requirements are satisfied
    # 2. No required skills are missing
    # --------------------------------------------------------

    eligible = (
        academic_result["academic_eligible"]
        and
        len(skill_result["missing_skills"]) == 0
    )

    return {
        "eligible": eligible,

        "matched_skills":
            skill_result["matched_skills"],

        "missing_skills":
            skill_result["missing_skills"],

        "academic_eligible":
            academic_result["academic_eligible"],

        "academic_failures":
            academic_result["academic_failures"]
    }