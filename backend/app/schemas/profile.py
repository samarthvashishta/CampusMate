
# schemas/profile.py


from pydantic import BaseModel, EmailStr


class ProfileUpdateRequest(BaseModel):
    """
    What the frontend sends to PUT /api/profile/me.
    Every field is optional, so a student can update just one
    field (e.g. only "skills") without resending everything else.
    """

    name: str | None = None
    email: EmailStr | None = None
    department: str | None = None
    semester: int | None = None
    skills: list[str] | None = None
    interests: list[str] | None = None
