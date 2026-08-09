from typing import TypedDict, List, Optional

from dotenv import load_dotenv

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from backend.rag.retriever import retrieve

from backend.agents.career_agent.eligibility import (
    evaluate_candidate
)

import os
import re
import json
import inspect


# ============================================================
# ENV
# ============================================================

load_dotenv()


# ============================================================
# LLM
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0,
    api_key=os.getenv("GEMINI_API_KEY"),
)


# ============================================================
# STATE
# ============================================================

class State(TypedDict, total=False):

    user_input: str
    resume_path: str

    company: str
    role: str

    cgpa: Optional[float]
    tenth: Optional[float]
    twelfth: Optional[float]

    skills: List[str]

    # RAG
    rag_context: str

    required_skills: List[str]
    academic_requirements: dict

    # Evaluation
    matched_skills: List[str]
    missing_skills: List[str]

    academic_eligible: bool
    academic_failures: List[str]

    eligible: bool

    missing_fields: List[str]

    answer: str

    unknown_role: bool


# ============================================================
# TEXT HELPER
# ============================================================

def to_text(reply):

    content = reply.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        return "".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
        )

    return str(content)


# ============================================================
# JSON HELPER
# ============================================================

def to_json(text):

    if not text:
        return {}

    text = str(text).strip()

    # Remove markdown code fences
    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```",
        "",
        text
    )

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:
        return {}

    try:
        return json.loads(
            match.group()
        )

    except Exception:
        return {}


# ============================================================
# NUMBER HELPER
# ============================================================

def to_number(value):

    if value is None:
        return None

    match = re.search(
        r"\d+(?:\.\d+)?",
        str(value)
    )

    if match:
        return float(
            match.group()
        )

    return None


# ============================================================
# READ RESUME
# ============================================================

def read_resume(path):

    if not path:
        return ""

    if not os.path.exists(path):
        return ""

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if path.lower().endswith(".pdf"):

        from pypdf import PdfReader

        reader = PdfReader(path)

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if path.lower().endswith(".docx"):

        from docx import Document

        document = Document(path)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    # --------------------------------------------------------
    # TXT
    # --------------------------------------------------------

    with open(
        path,
        encoding="utf-8",
        errors="ignore"
    ) as file:

        return file.read()


# ============================================================
# STEP 1
# READ PROFILE
# ============================================================

def read_profile(s: State) -> State:

    resume = read_resume(
        s.get("resume_path", "")
    )

    prompt = f"""
You are extracting a student's career profile.

Read BOTH the student message and resume.

Return ONLY valid JSON.

{{
    "company": null,
    "role": null,
    "cgpa": null,
    "tenth": null,
    "twelfth": null,
    "skills": []
}}

RULES:

1. Extract company if explicitly mentioned.

2. Extract role if explicitly mentioned.

3. Extract CGPA from the resume or message.

4. Extract 10th percentage from the resume
   or message.

5. Extract 12th percentage from the resume
   or message.

6. Extract technical skills.

7. Understand abbreviations semantically.

Examples:

ML = Machine Learning

DL = Deep Learning

ML/DL = Machine Learning and Deep Learning

MLOps = MLOps

Data Viz = Data Visualization

8. Do not invent information.

9. If something is unavailable, return null.

10. Return skills as a list of strings.

STUDENT MESSAGE:

{s["user_input"]}

RESUME:

{resume}
"""

    reply = llm.invoke(prompt)

    data = to_json(
        to_text(reply)
    )

    return {

        **s,

        "company":
            data.get("company") or "",

        "role":
            data.get("role") or "",

        "cgpa":
            to_number(
                data.get("cgpa")
            ),

        "tenth":
            to_number(
                data.get("tenth")
            ),

        "twelfth":
            to_number(
                data.get("twelfth")
            ),

        "skills":
            data.get("skills") or []
    }


# ============================================================
# STEP 2
# MISSING INFORMATION
# ============================================================

def ask_missing(s: State) -> State:

    required = {

        "company":
            "Company name",

        "role":
            "Role",

        "cgpa":
            "CGPA",

        "tenth":
            "10th percentage",

        "twelfth":
            "12th percentage",

        "skills":
            "Skills"
    }

    missing = []

    for field in required:

        value = s.get(field)

        if value is None:
            missing.append(field)

        elif value == "":
            missing.append(field)

        elif value == []:
            missing.append(field)

    if missing:

        message = (
            "Please tell me:\n\n"
            +
            "\n".join(
                "- " + required[field]
                for field in missing
            )
        )

        return {

            **s,

            "missing_fields":
                missing,

            "answer":
                message
        }

    return {

        **s,

        "missing_fields": []
    }


# ============================================================
# ROUTER
# ============================================================

def route_after_missing(s: State):

    if s.get("missing_fields"):
        return "ask"

    return "retrieve"


# ============================================================
# RETRIEVER ADAPTER
# ============================================================

def call_existing_retriever(query):

    """
    Calls the existing retrieve() function.

    Supports common signatures:

        retrieve(query)

        retrieve(collection, query)

        retrieve(query=query)
    """

    try:

        signature = inspect.signature(
            retrieve
        )

        parameters = list(
            signature.parameters.values()
        )

        required_parameters = [

            p

            for p in parameters

            if (
                p.default
                is inspect.Parameter.empty
            )

            and
            p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD
            )
        ]

        number = len(
            required_parameters
        )

        # ----------------------------------------------------
        # retrieve(query)
        # ----------------------------------------------------

        if number == 1:
            return retrieve(query)

        # ----------------------------------------------------
        # retrieve(collection, query)
        # ----------------------------------------------------

        if number == 2:
            return retrieve(
                "placement",
                query
            )

        # ----------------------------------------------------
        # Keyword query
        # ----------------------------------------------------

        return retrieve(
            query=query
        )

    except Exception as e:

        raise RuntimeError(
            f"""
Career Agent could not call the RAG retriever.

Original error:

{e}

Check rag/retriever.py and its retrieve()
function signature.
"""
        )


# ============================================================
# STEP 3
# RAG RETRIEVAL
# ============================================================

def retrieve_requirements(s: State) -> State:

    query = f"""
Company: {s["company"]}

Role: {s["role"]}

Find information specifically related to
this company and this role.

Retrieve:

- academic eligibility requirements
- minimum CGPA
- minimum 10th percentage
- minimum 12th percentage
- branch requirements
- required technical skills
- role-specific requirements

IMPORTANT:

Do not mix requirements from another company.

Do not mix requirements from another role.

Return the most relevant knowledge base
information.
"""

    context = call_existing_retriever(
        query
    )

    if isinstance(context, list):

        context = "\n\n".join(
            str(item)
            for item in context
        )

    elif context is None:

        context = ""

    else:

        context = str(context)

    return {

        **s,

        "rag_context":
            context
    }


# ============================================================
# STEP 4
# EXTRACT REQUIREMENTS FROM RAG
# ============================================================

def extract_requirements(s: State) -> State:

    context = s.get(
        "rag_context",
        ""
    )

    if not context.strip():

        return {

            **s,

            "required_skills": [],

            "academic_requirements": {},

            "unknown_role": True
        }

    prompt = f"""
You are extracting requirements from a
company career knowledge base.

Requested company:
{s["company"]}

Requested role:
{s["role"]}

Knowledge base context:

{context}

Return ONLY valid JSON.

{{
    "minimum_cgpa": null,
    "minimum_10th": null,
    "minimum_12th": null,
    "maximum_backlogs": null,
    "allowed_branches": [],
    "required_skills": []
}}

RULES:

1. Use ONLY information contained in the
   knowledge base context.

2. Extract requirements specifically related
   to the requested company and role.

3. Do not invent requirements.

4. Do not use general industry requirements
   as company requirements.

5. If a minimum CGPA is not available,
   return null.

6. If a 10th requirement is not available,
   return null.

7. If a 12th requirement is not available,
   return null.

8. Extract technical skills that are explicitly
   relevant to the role.

9. Keep skill names understandable and concise.

10. If role requirements are not present,
    return an empty required_skills list.
"""

    reply = llm.invoke(prompt)

    data = to_json(
        to_text(reply)
    )

    academic_requirements = {

        "minimum_cgpa":
            to_number(
                data.get("minimum_cgpa")
            ),

        "minimum_10th":
            to_number(
                data.get("minimum_10th")
            ),

        "minimum_12th":
            to_number(
                data.get("minimum_12th")
            ),

        "maximum_backlogs":
            data.get("maximum_backlogs"),

        "allowed_branches":
            data.get("allowed_branches")
            or []
    }

    required_skills = (
        data.get("required_skills")
        or []
    )

    # --------------------------------------------------------
    # Role is considered known if we found either:
    #
    # 1. skills
    # OR
    # 2. academic requirements
    # --------------------------------------------------------

    has_requirements = (
        bool(required_skills)
        or
        any(
            value is not None
            for key, value
            in academic_requirements.items()
            if key != "allowed_branches"
            and key != "maximum_backlogs"
        )
        or
        bool(
            academic_requirements[
                "allowed_branches"
            ]
        )
    )

    return {

        **s,

        "required_skills":
            required_skills,

        "academic_requirements":
            academic_requirements,

        "unknown_role":
            not has_requirements
    }


# ============================================================
# STEP 5
# EVALUATE
# ============================================================

def check_eligibility(s: State) -> State:

    if s.get("unknown_role"):

        return {

            **s,

            "matched_skills": [],

            "missing_skills": [],

            "academic_eligible": False,

            "academic_failures": [],

            "eligible": False
        }

    result = evaluate_candidate(

        student_skills=
            s["skills"],

        required_skills=
            s["required_skills"],

        cgpa=
            s["cgpa"],

        tenth=
            s["tenth"],

        twelfth=
            s["twelfth"],

        academic_requirements=
            s["academic_requirements"]
    )

    return {

        **s,

        "matched_skills":
            result["matched_skills"],

        "missing_skills":
            result["missing_skills"],

        "academic_eligible":
            result["academic_eligible"],

        "academic_failures":
            result["academic_failures"],

        "eligible":
            result["eligible"]
    }


# ============================================================
# STEP 6
# FINAL ANSWER
# ============================================================

def write_answer(s: State) -> State:

    # --------------------------------------------------------
    # UNKNOWN ROLE
    # --------------------------------------------------------

    if s.get("unknown_role"):

        s["answer"] = f"""
I could not find reliable requirements for
{s["company"]} - {s["role"]} in the knowledge base.

I cannot determine company-specific eligibility
without those requirements.

Please make sure the knowledge base contains
requirements for this company and role.
"""

        return s

    # --------------------------------------------------------
    # ACADEMIC RESULT
    # --------------------------------------------------------

    if s["academic_eligible"]:

        academic_result = "Eligible ✅"

    else:

        academic_result = "Not Eligible ❌"


    # --------------------------------------------------------
    # APPLICATION RESULT
    # --------------------------------------------------------

    if s["eligible"]:

        application_result = (
            "You can apply for this role. ✅"
        )

    elif not s["academic_eligible"]:

        application_result = (
            "You do not meet the academic "
            "requirements for this role. ❌"
        )

    else:

        application_result = (
            "You meet the academic requirements, "
            "but you should strengthen the missing "
            "skills before applying. ⚠️"
        )


    prompt = f"""
You are a career guidance assistant.

Company:
{s["company"]}

Role:
{s["role"]}

Student skills:
{s["skills"]}

Required skills from knowledge base:
{s["required_skills"]}

Matched skills:
{s["matched_skills"]}

Missing skills:
{s["missing_skills"]}

Academic result:
{academic_result}

Academic failures:
{s["academic_failures"]}

Academic requirements from knowledge base:
{s["academic_requirements"]}

Write a concise and practical response.

IMPORTANT RULES:

1. DO NOT calculate a score.

2. DO NOT mention percentages such as
   skill score or match score.

3. DO NOT invent requirements.

4. DO NOT add skills to the missing-skills list.

5. DO NOT remove skills from the missing-skills list.

6. DO NOT change the academic result.

7. Use the exact matched and missing skills
   provided by the system.

Explain:

1. Eligibility status
2. Matched skills
3. Missing skills
4. Whether the student can apply
5. What the student should learn next

Give a short preparation recommendation.
"""

    reply = llm.invoke(prompt)

    guide = to_text(reply)

    s["answer"] = (
        f"Academic Eligibility: "
        f"{academic_result}\n\n"
        f"{application_result}\n\n"
        f"{guide}"
    )

    return s


# ============================================================
# BUILD LANGGRAPH
# ============================================================

def build_agent():

    graph = StateGraph(State)

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    graph.add_node(
        "read_profile",
        read_profile
    )

    graph.add_node(
        "ask_missing",
        ask_missing
    )

    graph.add_node(
        "retrieve_requirements",
        retrieve_requirements
    )

    graph.add_node(
        "extract_requirements",
        extract_requirements
    )

    graph.add_node(
        "check_eligibility",
        check_eligibility
    )

    graph.add_node(
        "write_answer",
        write_answer
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "read_profile"
    )

    # --------------------------------------------------------
    # Profile -> Missing
    # --------------------------------------------------------

    graph.add_edge(
        "read_profile",
        "ask_missing"
    )

    # --------------------------------------------------------
    # Missing router
    # --------------------------------------------------------

    graph.add_conditional_edges(

        "ask_missing",

        route_after_missing,

        {
            "ask": END,

            "retrieve":
                "retrieve_requirements"
        }
    )

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    graph.add_edge(
        "retrieve_requirements",
        "extract_requirements"
    )

    # --------------------------------------------------------
    # Requirements -> Evaluation
    # --------------------------------------------------------

    graph.add_edge(
        "extract_requirements",
        "check_eligibility"
    )

    # --------------------------------------------------------
    # Evaluation -> Answer
    # --------------------------------------------------------

    graph.add_edge(
        "check_eligibility",
        "write_answer"
    )

    # --------------------------------------------------------
    # END
    # --------------------------------------------------------

    graph.add_edge(
        "write_answer",
        END
    )

    return graph.compile()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    agent = build_agent()

    resume = input(
        "Resume path (or press Enter to skip): "
    ).strip()

    query = input(
        "Ask: "
    ).strip()

    while True:

        result = agent.invoke({

            "user_input":
                query,

            "resume_path":
                resume
        })

        print(
            "\n"
            + result["answer"]
            + "\n"
        )

        # ----------------------------------------------------
        # Everything available
        # ----------------------------------------------------

        if not result.get(
            "missing_fields"
        ):

            break

        # ----------------------------------------------------
        # Collect missing information
        # ----------------------------------------------------

        for field in result[
            "missing_fields"
        ]:

            value = input(
                field + ": "
            ).strip()

            query += (
                f"\n{field}: {value}"
            )