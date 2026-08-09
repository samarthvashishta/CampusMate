# routers/profile.py

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_student
from app.schemas.auth import StudentPublic
from app.schemas.profile import ProfileUpdateRequest
from app.services import profile_service

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("/me", response_model=StudentPublic)
def get_my_profile(student: dict = Depends(get_current_student)):
    """Returns the logged-in student's own profile."""
    return profile_service.get_public_profile(student)


@router.put("/me", response_model=StudentPublic)
def update_my_profile(
    data: ProfileUpdateRequest,
    student: dict = Depends(get_current_student),
):
    """Updates the logged-in student's own profile."""
    return profile_service.update_profile(student, data)
