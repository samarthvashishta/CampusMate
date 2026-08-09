
# schemas/conversation.py


from datetime import datetime

from pydantic import BaseModel


class ConversationCreateRequest(BaseModel):
    """What the frontend sends to POST /api/conversations."""

    title: str = "New Chat"


class ConversationOut(BaseModel):
    """One row shown in the sidebar's conversation list."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    """One chat bubble."""

    id: str
    role: str
    content: str
    agent: str | None = None
    timestamp: datetime


class ConversationDetailOut(ConversationOut):
    """A single conversation together with its full message history."""

    messages: list[MessageOut] = []
