# -----------------------------------------------------------------
# dependencies.py
#
# A FastAPI "dependency" is a function that runs automatically
# before a route function, and can supply a value to it.
#
# get_current_student() reads the JWT from the Authorization header,
# verifies it, and loads the matching student from the database. Any
# route that adds `student = Depends(get_current_student)` to its
# arguments becomes a protected/logged-in-only route.
# -----------------------------------------------------------------

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.jwt_handler import decode_access_token
from app.database import get_db
from app.models.student import student_row_to_dict

# tokenUrl just tells the auto-generated docs (/docs) where a token
# can be obtained from - it does not change how we validate tokens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_student(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency used by protected routes. Returns the logged-in
    student's data as a dict, or raises 401 Unauthorized.
    """
    unauthorized_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    student_id = decode_access_token(token)
    if not student_id:
        raise unauthorized_error

    try:
        student_id = int(student_id)
    except ValueError:
        raise unauthorized_error

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()

    if not row:
        raise unauthorized_error

    return student_row_to_dict(row)
