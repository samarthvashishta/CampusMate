# -----------------------------------------------------------------
# ai_bridge.py
#
# This file is the ONLY place where the backend talks to the
# existing multi-agent AI system (router/router.py + agents/).
# That system is treated as a "black box" we do not modify - by
# keeping all of the wiring to it in this one file, the rest of the
# backend never needs to know how routing/agents work internally.
#
# What we import already exists in the repo:
#   - classify_intent(query)  -> "academic" | "wellness" | "career" | "startup"
#   - run_academic(query) / run_wellness(query) / run_startup(query)
#     -> each returns the agent's answer as a string
#   - run_career(query, resume_path="") -> the career agent's answer,
#     it reads the resume file at resume_path itself if one is given
#
# We call classify_intent() once and then call the matching
# run_*() function directly. This gives us back BOTH the answer
# text AND the name of the agent that produced it (needed for the
# "agent" field on assistant messages), using the exact same
# classification the router already performs internally - we are
# not writing any routing logic of our own.
# -----------------------------------------------------------------

from router.router import (
    classify_intent,
    run_academic,
    run_career,
    run_startup,
    run_wellness,
)
from app.utils.context_retrieval import add_context_to_message

_AGENT_FUNCTIONS = {
    "academic": run_academic,
    "wellness": run_wellness,
    "startup": run_startup,
}


def get_ai_response(message: str, profile: dict, history: list[dict], resume_path: str = "") -> tuple[str, str]:
    """
    Sends a student's message to the existing AI system and returns
    (answer_text, agent_name).

    Step 1: work out which agent should answer. If a resume file was
    attached (resume_path is set), it always goes to the career agent,
    which reads that file itself. Otherwise classify_intent() looks at
    the new message to pick the agent.
    Step 2: add_context_to_message() (see context_retrieval.py) glues
    this student's earlier conversation in front of the new message,
    so the agent that actually answers can see what was said before.
    """
    agent_name = "career" if resume_path else classify_intent(message)
    message_with_context = add_context_to_message(message, history)

    if agent_name == "career":
        answer = run_career(message_with_context, resume_path)
    else:
        agent_function = _AGENT_FUNCTIONS.get(agent_name, run_academic)
        answer = agent_function(message_with_context)

    return answer, agent_name
