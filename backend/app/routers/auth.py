# -----------------------------------------------------------------
# routers/auth.py
#
# HTTP routes for signup and login. These functions stay "thin" -
# they just read the request, call the service layer, and return
# the response. All the real work happens in services/auth_service.py.
# -----------------------------------------------------------------

from fastapi import APIRouter

from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse)
def signup(data: SignupRequest):
    """Creates a new student account and logs them in immediately."""
    token, student = auth_service.signup_student(data)
    return {"access_token": token, "student": student}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    """Logs a student in using roll_number + password."""
    token, student = auth_service.login_student(data)
    return {"access_token": token, "student": student}
