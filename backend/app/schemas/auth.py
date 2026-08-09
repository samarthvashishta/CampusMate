# Pydantic schemas = shapes of the JSON that comes IN to and goes
# OUT of our API. FastAPI uses these to validate requests
# automatically and to generate the /docs page.

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """What the frontend sends to POST /api/auth/signup."""

    roll_number: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    email: EmailStr
    department: str
    semester: int
    skills: list[str] = []
    interests: list[str] = []
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    """What the frontend sends to POST /api/auth/login."""

    roll_number: str
    password: str


class StudentPublic(BaseModel):
    """Student information that is safe to send back to the frontend
    (notice there is no password_hash field here)."""

    id: str
    roll_number: str
    name: str
    email: EmailStr
    department: str
    semester: int
    skills: list[str]
    interests: list[str]


class TokenResponse(BaseModel):
    """What we send back after a successful signup/login."""

    access_token: str
    token_type: str = "bearer"
    student: StudentPublic
