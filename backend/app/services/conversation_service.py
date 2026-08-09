# logic for creating conversations, listing a student's
# past conversations (for the sidebar), and loading one
# conversation's full message history.

from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.database import get_db
from app.models.conversation import conversation_row_to_dict
from app.models.message import message_row_to_dict


def create_conversation(student_id: str, title: str) -> dict:
    """Creates a new, empty conversation for a student."""
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO conversations (student_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (int(student_id), title, now, now),
        )
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (new_id,)
        ).fetchone()

    return conversation_row_to_dict(row)


def list_conversations(student_id: str) -> list[dict]:
    """Returns a student's conversations, most recently updated first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE student_id = ? ORDER BY updated_at DESC",
            (int(student_id),),
        ).fetchall()

    return [conversation_row_to_dict(row) for row in rows]


def get_conversation_or_404(student_id: str, conversation_id: str) -> dict:
    """Loads a conversation and makes sure it belongs to the current student."""
    try:
        numeric_id = int(conversation_id)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (numeric_id,)
        ).fetchone()

    if not row or row["student_id"] != int(student_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    return conversation_row_to_dict(row)


def get_conversation_detail(student_id: str, conversation_id: str) -> dict:
    """Returns a conversation together with its full message history,
    in the order the messages were sent."""
    conversation = get_conversation_or_404(student_id, conversation_id)

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (int(conversation_id),),
        ).fetchall()

    conversation["messages"] = [message_row_to_dict(row) for row in rows]
    return conversation


def get_history_for_ai(conversation_id: str) -> list[dict]:
    """Returns past messages of a conversation as simple {role, content}
    dicts, to give the AI system conversation context."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (int(conversation_id),),
        ).fetchall()

    return [{"role": row["role"], "content": row["content"]} for row in rows]


def add_message(conversation_id: str, role: str, content: str, agent: str | None = None) -> dict:
    """Saves one chat message (either role="user" or role="assistant")."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO messages (conversation_id, role, content, agent, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (int(conversation_id), role, content, agent, datetime.now(timezone.utc).isoformat()),
        )
        new_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (new_id,)).fetchone()

    return message_row_to_dict(row)


def touch_conversation(conversation_id: str) -> None:
    """Updates a conversation's "updated_at" timestamp, so the sidebar
    can sort by most recently active conversation."""
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), int(conversation_id)),
        )
