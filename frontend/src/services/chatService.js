// -----------------------------------------------------------------
// chatService.js
//
// All API calls related to conversations and chatting with the AI.
// -----------------------------------------------------------------

import api from "./api";

export async function createConversation(title = "New Chat") {
  const response = await api.post("/conversations", { title });
  return response.data;
}

export async function listConversations() {
  const response = await api.get("/conversations");
  return response.data;
}

export async function getConversation(conversationId) {
  const response = await api.get(`/conversations/${conversationId}`);
  return response.data;
}

// resumeFile is optional (a browser File object from an <input type="file">).
// Sent as multipart form data (not JSON) so it can carry a real file,
// same as a normal chatbot's "type message + attach file" box.
export async function sendMessage(message, conversationId, resumeFile) {
  const formData = new FormData();
  formData.append("message", message);
  if (conversationId) formData.append("conversation_id", conversationId);
  if (resumeFile) formData.append("resume", resumeFile);

  const response = await api.post("/chat", formData);
  return response.data; // { conversation_id, answer, agent, timestamp }
}
