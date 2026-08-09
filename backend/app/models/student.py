# models/student.py
#
# Everything related to the shape of a "student" row in SQLite.
#
# SQLite has no built-in list type, so "skills" and "interests"
# (which are lists in our API) are stored as a JSON-encoded TEXT
# column, e.g. '["Python", "SQL"]'. json.dumps()/json.loads() convert
# between a Python list and that stored text.

import json

CREATE_STUDENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    skills TEXT NOT NULL,
    interests TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def student_row_to_dict(row) -> dict:
    """Converts one SQLite row from the students table into a plain dict."""
    return {
        "id": str(row["id"]),
        "roll_number": row["roll_number"],
        "name": row["name"],
        "email": row["email"],
        "department": row["department"],
        "semester": row["semester"],
        "skills": json.loads(row["skills"]),
        "interests": json.loads(row["interests"]),
        "password_hash": row["password_hash"],
        "created_at": row["created_at"],
    }
