// -----------------------------------------------------------------
// ChatWindow.jsx
//
// Main chat area: the scrolling list of messages plus the text
// input box at the bottom used to send a new message. Also has an
// "Add File" button (like a normal chatbot) so a student can attach
// their resume (.pdf/.docx/.txt) - the file is uploaded together with
// the message, and the career agent reads it and checks eligibility.
// -----------------------------------------------------------------

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages, onSendMessage, isSending }) {
  const [draft, setDraft] = useState("");
  const [attachedFile, setAttachedFile] = useState(null); // browser File object
  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-scroll to the newest message whenever the message list changes.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleAttachClick() {
    fileInputRef.current?.click();
  }

  function handleFileChange(event) {
    const file = event.target.files[0];
    event.target.value = ""; // allow attaching the same file again later
    if (file) setAttachedFile(file);
  }

  function handleSubmit(event) {
    event.preventDefault();
    const text = draft.trim();
    if (isSending || (!text && !attachedFile)) return;

    onSendMessage(text, attachedFile);
    setDraft("");
    setAttachedFile(null);
  }

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            Ask me anything about academics, career, wellness or startups!
            Attach your resume (.pdf, .docx or .txt) to check your eligibility.
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            role={message.role}
            content={message.content}
            agent={message.agent}
          />
        ))}

        {isSending && (
          <div className="message-row message-row-assistant">
            <div className="message-bubble message-bubble-assistant message-bubble-loading">
              Thinking...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {attachedFile && (
        <div className="chat-attachment-chip">
          📎 {attachedFile.name}
          <button type="button" onClick={() => setAttachedFile(null)}>
            ×
          </button>
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <button type="button" className="chat-send-button" onClick={handleAttachClick}>
          Add File
        </button>
        <input
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={isSending}
        />
        <button type="submit" className="chat-send-button" disabled={isSending}>
          Send
        </button>
      </form>
    </div>
  );
}
