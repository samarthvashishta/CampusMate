# -----------------------------------------------------------------
# models/conversation.py
# -----------------------------------------------------------------

CREATE_CONVERSATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id)
)
"""


def conversation_row_to_dict(row) -> dict:
    """Converts one SQLite row from the conversations table into a plain dict."""
    return {
        "id": str(row["id"]),
        "student_id": str(row["student_id"]),
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
