// -----------------------------------------------------------------
// Sidebar.jsx
//
// Left panel of the Chat page: a "New Chat" button and the list of
// the student's previous conversations, loaded from the backend.
// -----------------------------------------------------------------

import { useNavigate, useParams } from "react-router-dom";

export default function Sidebar({ conversations, onNewChat }) {
  const navigate = useNavigate();
  const { conversationId } = useParams();

  return (
    <aside className="sidebar">
      <button className="sidebar-new-chat" onClick={onNewChat}>
        + New Chat
      </button>

      <div className="sidebar-list">
        {conversations.length === 0 && (
          <p className="sidebar-empty">No conversations yet</p>
        )}

        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            className={
              "sidebar-item" +
              (conversation.id === conversationId ? " sidebar-item-active" : "")
            }
            onClick={() => navigate(`/chat/${conversation.id}`)}
          >
            {conversation.title || "Untitled chat"}
          </button>
        ))}
      </div>
    </aside>
  );
}
