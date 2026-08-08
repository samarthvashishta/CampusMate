# -----------------------------------------------------------------
# jwt_handler.py
#
# Creates and reads JWT ("JSON Web Token") access tokens.
#
# How it works (simple version):
# 1. When a student logs in successfully, we create a token that
#    contains their student id and an expiry time, signed with our
#    secret key.
# 2. The frontend stores this token and sends it back on every
#    request in the "Authorization: Bearer <token>" header.
# 3. On each protected request, we decode the token and check the
#    signature + expiry to know who is calling the API.
# -----------------------------------------------------------------

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES


def create_access_token(student_id: str) -> str:
    """Builds a signed JWT for the given student id."""
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)

    # "sub" (subject) is the standard JWT field for "who is this token about".
    payload = {"sub": student_id, "exp": expire_at}

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> str | None:
    """
    Verifies a JWT and returns the student id stored inside it.
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
