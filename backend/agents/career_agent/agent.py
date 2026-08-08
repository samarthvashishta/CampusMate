from typing import TypedDict, List, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.agents.career_agent.eligibility import ROLES, _canon
import os, re, json

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0,
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Marks weightage (total = 100)
SKILLS = 50
CGPA = 20
TENTH = 15
TWELFTH = 15


# ---------- State: the memory box that flows through every step ----------
class State(TypedDict, total=False):
    user_input: str
    resume_path: str          # <-- NEW
    company: str
    role: str
    cgpa: Optional[float]
    tenth: Optional[float]
    twelfth: Optional[float]
    skills: List[str]
    missing_skills: List[str]
    score: float
    verdict: str
    missing_fields: List[str]
    answer: str


# ---------- tiny helpers ----------
def to_text(reply):
    # Gemini reply -> plain text
    c = reply.content
    return c if isinstance(c, str) else c[0]["text"]

def to_json(t):
    # pull the {...} out of the reply
    m = re.search(r"\{.*\}", t, re.DOTALL)
    return json.loads(m.group()) if m else {}

def to_number(v):
    # "85%" -> 85.0
    if v is None:
        return None
    m = re.search(r"\d+(\.\d+)?", str(v))
    return float(m.group()) if m else None

def read_resume(path):                       # <-- NEW
    # open PDF / DOCX / TXT and return its text
    if not path or not os.path.exists(path):
        return ""
    if path.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    if path.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(path).paragraphs)
    return open(path, encoding="utf-8", errors="ignore").read()


# ---------- Step 1: read the student's details (message + resume) ----------
def read_profile(s: State) -> State:
    resume = read_resume(s.get("resume_path", ""))        # <-- NEW

    reply = llm.invoke(f"""
Read this student message and resume, return ONLY JSON:
{{"company":null,"role":null,"cgpa":null,"tenth":null,"twelfth":null,"skills":[]}}

Message: {s["user_input"]}

Resume: {resume}
""")
    d = to_json(to_text(reply))
    return {**s,
        "company": d.get("company") or "",
        "role": d.get("role") or "",
        "cgpa": to_number(d.get("cgpa")),
        "tenth": to_number(d.get("tenth")),
        "twelfth": to_number(d.get("twelfth")),
        "skills": d.get("skills") or [],
    }


# ---------- Step 2: ask for anything missing ----------
def ask_missing(s: State) -> State:
    need = {
        "company": "Company name (example: TCS)",
        "role": "Role (example: Data Analyst)",
        "cgpa": "CGPA (example: 7.5)",
        "tenth": "10th percentage (example: 85%)",
        "twelfth": "12th percentage (example: 80%)",
        "skills": "Skills (example: SQL, Excel)",
    }
    missing = [f for f in need if not s.get(f)]
    if missing:
        msg = "Please tell me:\n" + "\n".join("- " + need[f] for f in missing)
        return {**s, "missing_fields": missing, "answer": msg}
    return {**s, "missing_fields": []}

def is_something_missing(s: State) -> str:
    return "ask" if s.get("missing_fields") else "check"


# ---------- Step 3: check eligibility with marks ----------
def check_eligibility(s: State) -> State:
    # what skills does this role need?
    needed = ROLES.get(s["role"].title(), {"SQL": 100})
    have = {_canon(x) for x in s["skills"]}

    matched = [k for k in needed if _canon(k) in have]
    missing = [k for k in needed if _canon(k) not in have]

    # skill part of the score
    skill_marks = len(matched) / len(needed) * SKILLS

    # add marks for grades
    score = skill_marks
    score += CGPA if (s["cgpa"] and s["cgpa"] >= 6) else 0
    score += TENTH if (s["tenth"] and s["tenth"] >= 60) else 0
    score += TWELFTH if (s["twelfth"] and s["twelfth"] >= 60) else 0

    verdict = "Eligible ✅" if score >= 80 else "Not Eligible ❌"

    return {**s,
        "missing_skills": missing,
        "score": round(score, 1),
        "verdict": verdict,
    }


# ---------- Step 4: write the final answer ----------
def write_answer(s: State) -> State:
    reply = llm.invoke(f"""
Student wants: {s['company']} {s['role']}
Result: {s['verdict']} with score {s['score']}/100
Missing skills: {s['missing_skills']}

Write a short friendly guide:
1. Result
2. Skills to learn
3. A simple 7-day plan
4. 5 interview questions
""")
    guide = to_text(reply)
    s["answer"] = f"Score: {s['score']}/100\nResult: {s['verdict']}\n\n{guide}"
    return s


# ---------- Build the flow ----------
def build_agent():
    g = StateGraph(State)
    g.add_node("read_profile", read_profile)
    g.add_node("ask_missing", ask_missing)
    g.add_node("check_eligibility", check_eligibility)
    g.add_node("write_answer", write_answer)

    g.add_edge(START, "read_profile")
    g.add_edge("read_profile", "ask_missing")
    g.add_conditional_edges("ask_missing", is_something_missing,
                            {"ask": END, "check": "check_eligibility"})
    g.add_edge("check_eligibility", "write_answer")
    g.add_edge("write_answer", END)
    return g.compile()


# ---------- Run it ----------
if __name__ == "__main__":
    agent = build_agent()

    resume = input("Resume path (or press Enter to skip): ").strip()   # <-- NEW
    query = input("Ask: ") or "I want TCS Data Analyst"

    while True:
        result = agent.invoke({"user_input": query, "resume_path": resume})   # <-- resume added

        print("\n" + result["answer"] + "\n")

        if not result.get("missing_fields"):
            break

        for field in result["missing_fields"]:
            query += f"\n{field}: {input(field + ': ')}"