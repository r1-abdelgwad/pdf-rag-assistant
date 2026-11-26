import { useEffect, useState } from "react";
import { deleteDocument, getHealth, listDocuments, sendChat, uploadDocument } from "./api";
import ChatWindow from "./components/ChatWindow.jsx";
import DocumentPanel from "./components/DocumentPanel.jsx";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
  const [keyMissing, setKeyMissing] = useState(false);

  useEffect(() => {
    listDocuments().then(setDocuments).catch((e) => setNotice(e.message));
    getHealth().then((h) => setKeyMissing(!h.llm_configured)).catch(() => {});
  }, []);

  async function handleUpload(file) {
    setNotice("");
    setUploading(true);
    try {
      await uploadDocument(file);
      setDocuments(await listDocuments());
    } catch (e) {
      setNotice(e.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(filename) {
    setNotice("");
    try {
      await deleteDocument(filename);
      setDocuments(await listDocuments());
    } catch (e) {
      setNotice(e.message);
    }
  }

  async function handleSend(text) {
    // The backend is stateless: we send the earlier messages with every request.
    const history = messages
      .filter((m) => !m.error)
      .map(({ role, content }) => ({ role, content }));

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const { answer, sources } = await sendChat(text, history);
      setMessages((prev) => [...prev, { role: "assistant", content: answer, sources }]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", content: e.message, error: true }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="app">
      <DocumentPanel
        documents={documents}
        uploading={uploading}
        onUpload={handleUpload}
        onDelete={handleDelete}
      />
      <main className="chat">
        {keyMissing && (
          <div className="banner warning">
            The LLM is not configured. Add GROQ_API_KEY to backend/.env and restart the backend.
          </div>
        )}
        {notice && (
          <div className="banner error" role="alert">
            {notice}
            <button onClick={() => setNotice("")} aria-label="Dismiss">×</button>
          </div>
        )}
        <ChatWindow
          messages={messages}
          sending={sending}
          hasDocuments={documents.length > 0}
          onSend={handleSend}
          onClear={() => setMessages([])}
        />
      </main>
    </div>
  );
}
