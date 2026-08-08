# -----------------------------------------------------------------
# services/auth_service.py
#
# Business logic for signup/login. Routers stay thin (just handle
# the HTTP request/response) and call into these functions to do
# the actual work.
# -----------------------------------------------------------------

import json
import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password, verify_password
from app.database import get_db
from app.models.student import student_row_to_dict
from app.schemas.auth import LoginRequest, SignupRequest


def signup_student(data: SignupRequest) -> tuple[str, dict]:
    """
    Creates a new student account.
    Returns (access_token, student_dict_without_password).
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO students
                    (roll_number, name, email, department, semester,
                     skills, interests, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.roll_number,
                    data.name,
                    data.email,
                    data.department,
                    data.semester,
                    json.dumps(data.skills),
                    json.dumps(data.interests),
                    hash_password(data.password),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # "roll_number" is UNIQUE in the table, so this fires if it's already taken.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this roll number already exists",
        )

    token = create_access_token(str(new_id))

    with get_db() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (new_id,)).fetchone()

    return token, _to_public_student(row)


def login_student(data: LoginRequest) -> tuple[str, dict]:
    """
    Checks roll number + password and returns (access_token, student_dict).
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE roll_number = ?", (data.roll_number,)
        ).fetchone()

    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid roll number or password",
    )

    if not row or not verify_password(data.password, row["password_hash"]):
        raise invalid_credentials_error

    token = create_access_token(str(row["id"]))
    return token, _to_public_student(row)


def _to_public_student(row) -> dict:
    """Removes the password hash before sending a student back to the frontend."""
    public_data = student_row_to_dict(row)
    public_data.pop("password_hash", None)
    return public_data
