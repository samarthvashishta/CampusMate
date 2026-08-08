# -----------------------------------------------------------------
# context_retrieval.py
#
# Simple, beginner-friendly helper.
#
# Every conversation in the database already belongs to exactly one
# student (see conversation_service.get_conversation_or_404), so the
# "history" list this file receives is ALWAYS that one student's own
# conversation. That is what makes this "per user" - we never mix
# messages from different students together.
#
# What this file does:
#   1. Turns the student's past messages into a plain text transcript.
#   2. Glues that transcript in front of the student's new question.
# That way, when the combined text is sent to the AI agents, the
# agent can see the earlier conversation and answer things like
# "what did I ask you before?" or "summarize our chat so far".
# -----------------------------------------------------------------

MAX_HISTORY_MESSAGES = 20  # keep prompts small and simple


def build_context_text(history: list[dict]) -> str:
    """Turns a list of {role, content} messages into a readable transcript."""
    if not history:
        return ""

    recent_messages = history[-MAX_HISTORY_MESSAGES:]

    lines = []
    for msg in recent_messages:
        speaker = "Student" if msg["role"] == "user" else "CampusMate"
        lines.append(f"{speaker}: {msg['content']}")
    transcript = "\n".join(lines)

    return (
        "----- earlier conversation with this student -----\n"
        f"{transcript}\n"
        "----- end of earlier conversation -----\n\n"
        "If the student asks what they said earlier, or asks for a "
        "summary of the chat, answer using the transcript above.\n\n"
    )


def add_context_to_message(message: str, history: list[dict]) -> str:
    """Combines the earlier conversation (if any) with the new question,
    so it can be sent to the AI agents as a single piece of text."""
    context_text = build_context_text(history)
    if not context_text:
        return message
    return f"{context_text}New question from the student:\n{message}"
