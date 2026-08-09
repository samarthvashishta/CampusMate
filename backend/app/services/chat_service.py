# This is the heart of the chat feature. It follows the flow:
#   1. (authentication already done by the router's Depends())
#   2. get the student profile
#   3. get the conversation history
#   4. if a resume file was attached, save it to a temp file on disk
#      (the career agent reads resumes from a file path)
#   5. send message + profile + history + resume path to the AI system
#   6. receive the AI's answer
#   7. save the student's message to the database
#   8. save the AI's answer to the database
#   9. update the conversation's "updated_at" timestamp
#  10. return the answer to the router, which sends it to the frontend

import os
import tempfile

from app.services import conversation_service
from app.utils.ai_bridge import get_ai_response


def send_message(student: dict, message: str, conversation_id: str | None, resume=None) -> dict:
    student_id = student["id"]

    # Step: if no conversation was picked, start a new one. The title
    # is just the start of the first message, trimmed to a short length.
    if conversation_id:
        conversation_service.get_conversation_or_404(student_id, conversation_id)
    else:
        title = message.strip()[:40] or (resume.filename if resume else "New Chat")
        conversation = conversation_service.create_conversation(student_id, title)
        conversation_id = conversation["id"]

    # Step: get conversation history (previous messages) for AI context.
    history = conversation_service.get_history_for_ai(conversation_id)

    # Step: build a small, safe profile dict (no password hash) to give the AI context.
    profile = {
        "name": student.get("name"),
        "department": student.get("department"),
        "semester": student.get("semester"),
        "skills": student.get("skills", []),
        "interests": student.get("interests", []),
    }

    # Step: if a resume was attached, save it to a temp file so the
    # career agent can open it (it reads .pdf/.docx/.txt from a path).
    resume_path = ""
    if resume is not None:
        suffix = os.path.splitext(resume.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(resume.file.read())
            resume_path = tmp_file.name

    try:
        # Step: send message + profile + history + resume to the AI system.
        answer, agent_name = get_ai_response(
            message=message, profile=profile, history=history, resume_path=resume_path
        )
    finally:
        if resume_path:
            os.remove(resume_path)

    # Step: save both the student's question and the AI's answer. If a
    # resume was attached, note that in the saved message so the chat
    # history shows it was there.
    saved_message = f"📎 {resume.filename}\n{message}" if resume is not None else message
    conversation_service.add_message(conversation_id, role="user", content=saved_message)
    assistant_message = conversation_service.add_message(
        conversation_id, role="assistant", content=answer, agent=agent_name
    )

    # Step: update the conversation's "last active" timestamp.
    conversation_service.touch_conversation(conversation_id)

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "agent": agent_name,
        "timestamp": assistant_message["timestamp"],
    }
