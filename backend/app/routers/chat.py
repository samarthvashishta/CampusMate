# routers/chat.py
#
# The main chat endpoint. See services/chat_service.py for the full
# step-by-step flow (get profile -> get history -> ask AI -> save
# messages -> return answer).


from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.auth.dependencies import get_current_student
from app.schemas.chat import ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# Plain form fields (not a JSON body) so the same request can also carry
# an attached resume file, like a normal chatbot's "type message + attach
# file" box. conversation_id/resume are optional - a plain text message
# with no file works exactly as before.
@router.post("", response_model=ChatResponse)
def chat(
    message: str = Form(""),
    conversation_id: str | None = Form(None),
    resume: UploadFile | None = File(None),
    student: dict = Depends(get_current_student),
):
    return chat_service.send_message(
        student=student,
        message=message,
        conversation_id=conversation_id,
        resume=resume,
    )
