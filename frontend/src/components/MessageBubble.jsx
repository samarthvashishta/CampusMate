// Renders a single chat message. Styled differently depending on
// whether it was sent by the student ("user") or the AI ("assistant").
// Assistant output is parsed as markdown (bold, lists, headings,
// tables, code). User messages stay plain text.


import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MessageBubble({ role, content, agent }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row-user" : "message-row-assistant"}`}>
      <div className={`message-bubble ${isUser ? "message-bubble-user" : "message-bubble-assistant"}`}>
        {!isUser && agent && <div className="message-agent-tag">{agent} agent</div>}

        {isUser ? (
          <p className="message-text">{content}</p>
        ) : (
          <div className="message-text markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}