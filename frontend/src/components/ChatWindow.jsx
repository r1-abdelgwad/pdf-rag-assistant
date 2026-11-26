import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ messages, sending, hasDocuments, onSend, onClear }) {
  const [text, setText] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  function submit() {
    const value = text.trim();
    if (!value || sending) return;
    setText("");
    onSend(value);
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <>
      <div className="messages">
        {messages.length === 0 && (
          <div className="empty">
            <h2>{hasDocuments ? "Ask about your documents" : "Start by uploading a PDF"}</h2>
            <p className="muted">
              {hasDocuments
                ? "Answers come only from your PDFs, with the page they were found on."
                : "Use the panel on the left. Then ask your question here."}
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {sending && <div className="bubble assistant typing">Thinking…</div>}
        <div ref={endRef} />
      </div>

      <div className="composer">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a question…  (Enter to send, Shift+Enter for a new line)"
          rows={2}
          maxLength={2000}
          dir="auto"
        />
        <div className="composer-actions">
          <button className="ghost" onClick={onClear} disabled={messages.length === 0}>
            Clear chat
          </button>
          <button className="primary" onClick={submit} disabled={sending || !text.trim()}>
            Send
          </button>
        </div>
      </div>
    </>
  );
}
