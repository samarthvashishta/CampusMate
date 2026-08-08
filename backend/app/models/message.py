# -----------------------------------------------------------------
# models/message.py
# -----------------------------------------------------------------

CREATE_MESSAGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    agent TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
)
"""


def message_row_to_dict(row) -> dict:
    """Converts one SQLite row from the messages table into a plain dict."""
    return {
        "id": str(row["id"]),
        "conversation_id": str(row["conversation_id"]),
        "role": row["role"],
        "content": row["content"],
        "agent": row["agent"],
        "timestamp": row["timestamp"],
    }
