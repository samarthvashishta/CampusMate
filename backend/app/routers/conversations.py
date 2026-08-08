# -----------------------------------------------------------------
# routers/conversations.py
# -----------------------------------------------------------------

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_student
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationDetailOut,
    ConversationOut,
)
from app.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationOut)
def create_conversation(
    data: ConversationCreateRequest,
    student: dict = Depends(get_current_student),
):
    """Starts a new, empty conversation."""
    return conversation_service.create_conversation(student["id"], data.title)


@router.get("", response_model=list[ConversationOut])
def list_conversations(student: dict = Depends(get_current_student)):
    """Lists the logged-in student's conversations (for the sidebar)."""
    return conversation_service.list_conversations(student["id"])


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: str,
    student: dict = Depends(get_current_student),
):
    """Loads one conversation with its full message history."""
    return conversation_service.get_conversation_detail(
        student["id"], conversation_id
    )
