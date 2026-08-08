from dotenv import load_dotenv
import os

from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from rag.retriever import retrieve

# =========================
# ENV
# =========================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# =========================
# LLM
# =========================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0,
    api_key=api_key,
)

# =========================
# RETRIEVER
# =========================

def get_context(query: str) -> str:
    try:
        context = retrieve("wellness", query)

        print("\n========== RETRIEVED CONTEXT ==========\n")
        print(context)
        print("\n=======================================\n")

        if not context:
            return "No wellness information found."

        return context

    except Exception as e:
        return f"Retriever Error: {str(e)}"


# =========================
# WELLNESS TOOL
# =========================

@tool
def wellness_rag(query: str) -> str:
    """
    Use for:
    stress
    anxiety
    sleep
    counselling
    wellness plans
    health routines
    mindfulness
    mood support
    exercise
    wellbeing
    """

    context = get_context(query)

    prompt = f"""
You are an expert Wellness Coach.

STRICT RULES:

1. Use ONLY the supplied context.
2. Do NOT say:
   - "I'm sorry"
   - "I understand"
   - "How are you feeling?"
3. Do NOT act like a therapist.
4. Create ACTIONABLE plans.
5. Use headings.
6. Use bullet points.
7. Be practical.
8. Maximum 350 words.

Generate response in this exact format:

# Wellness Assessment

Brief summary of user's issue.

# Immediate Actions (Today)

3-5 actions.

# Recommended Activities

Specific wellness activities.

# Daily Wellness Routine

Morning:
- item

Work Hours:
- item

Evening:
- item

# 21-Day Improvement Plan

Give habit-building suggestions.

# Professional Support

Mention support only if relevant.

CONTEXT:
{context}

USER QUERY:
{query}
"""

    response = llm.invoke(prompt)

    return response.content


# =========================
# AGENT
# =========================

agent = create_agent(
    model=llm,
    tools=[wellness_rag],
    system_prompt="""
You are CampusMate Wellness Agent.

RULES:

- ALWAYS call wellness_rag tool.
- NEVER answer directly.
- Use retrieved knowledge.
- Produce structured wellness plans.
"""
)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    query = input("Ask Wellness Agent: ")

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
    )

    print("\n================ RESPONSE ================\n")

    final_msg = response["messages"][-1].content

    if isinstance(final_msg, str):
        print(final_msg)
    else:
        print(final_msg[0]["text"])

    print("\n==========================================\n")