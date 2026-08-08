// -----------------------------------------------------------------
// Chat.jsx
//
// The main ChatGPT-like page: Navbar on top, Sidebar of previous
// conversations on the left, and the active conversation's messages
// + input box in the middle (ChatWindow).
// -----------------------------------------------------------------

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import * as chatService from "../services/chatService";

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  // Load the sidebar's conversation list once when the page mounts.
  useEffect(() => {
    loadConversations();
  }, []);

  // Whenever the conversation id in the URL changes, load that
  // conversation's messages (or clear them for a brand new chat).
  useEffect(() => {
    if (conversationId) {
      chatService.getConversation(conversationId).then((conversation) => {
        setMessages(conversation.messages);
      });
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  async function loadConversations() {
    const data = await chatService.listConversations();
    setConversations(data);
  }

  function handleNewChat() {
    navigate("/chat");
  }

  async function handleSendMessage(text, resumeFile) {
    setError("");

    // Show the student's own message immediately, without waiting
    // for the backend, so the chat feels responsive.
    const optimisticMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: resumeFile ? `📎 ${resumeFile.name}\n${text}` : text,
    };
    setMessages((current) => [...current, optimisticMessage]);
    setIsSending(true);

    try {
      const response = await chatService.sendMessage(text, conversationId, resumeFile);

      const assistantMessage = {
        id: `local-${Date.now()}-assistant`,
        role: "assistant",
        content: response.answer,
        agent: response.agent,
      };
      setMessages((current) => [...current, assistantMessage]);

      // If this message started a brand new conversation, move the
      // browser to its URL so refreshing the page keeps it open.
      if (!conversationId) {
        navigate(`/chat/${response.conversation_id}`, { replace: true });
      }

      // Refresh the sidebar so the new/updated conversation shows up.
      loadConversations();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send message.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="page-with-navbar">
      <Navbar />
      <div className="chat-layout">
        <Sidebar conversations={conversations} onNewChat={handleNewChat} />
        <div className="chat-main">
          {error && <p className="auth-error">{error}</p>}
          <ChatWindow
            messages={messages}
            onSendMessage={handleSendMessage}
            isSending={isSending}
          />
        </div>
      </div>
    </div>
  );
}
