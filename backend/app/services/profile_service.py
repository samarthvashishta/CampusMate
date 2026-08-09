import json

from app.database import get_db
from app.models.student import student_row_to_dict
from app.schemas.profile import ProfileUpdateRequest

# Maps API field names to the column name in the "students" table.
# skills/interests need json.dumps() because SQLite stores them as TEXT.
_UPDATABLE_FIELDS = ["name", "email", "department", "semester", "skills", "interests"]


def get_public_profile(student: dict) -> dict:
    """Removes the password hash before sending the profile to the frontend."""
    public_data = dict(student)
    public_data.pop("password_hash", None)
    return public_data


def update_profile(student: dict, data: ProfileUpdateRequest) -> dict:
    """
    Updates only the fields the student actually sent (exclude_unset=True
    skips any field that was left out of the request body), then
    returns the fresh profile.
    """
    updates = data.model_dump(exclude_unset=True)

    if updates:
        set_clauses = []
        values = []
        for field in _UPDATABLE_FIELDS:
            if field in updates:
                value = updates[field]
                if field in ("skills", "interests"):
                    value = json.dumps(value)
                set_clauses.append(f"{field} = ?")
                values.append(value)

        values.append(int(student["id"]))

        with get_db() as conn:
            conn.execute(
                f"UPDATE students SET {', '.join(set_clauses)} WHERE id = ?",
                values,
            )

    with get_db() as conn: #database connection----<
        row = conn.execute(
            "SELECT * FROM students WHERE id = ?", (int(student["id"]),)
        ).fetchone()

    return get_public_profile(student_row_to_dict(row))
