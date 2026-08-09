
# schemas/chat.py


from datetime import datetime

from pydantic import BaseModel


class ChatResponse(BaseModel):
    """The AI's reply, plus which conversation it belongs to."""

    conversation_id: str
    answer: str
    agent: str
    timestamp: datetime
