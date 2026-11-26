import { useRef, useState } from "react";

export default function DocumentPanel({ documents, uploading, onUpload, onDelete }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function pick(files) {
    Array.from(files).forEach(onUpload);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <aside className="sidebar">
      <h1>PDF Chatbot</h1>
      <p className="muted">Upload PDFs, then ask questions about them.</p>

      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files); }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => pick(e.target.files)}
        />
        <button className="primary" disabled={uploading} onClick={() => inputRef.current.click()}>
          {uploading ? "Processing…" : "Upload PDF"}
        </button>
        <span className="muted small">or drop files here</span>
      </div>

      <h2>Documents</h2>
      {documents.length === 0 ? (
        <p className="muted small">No documents yet.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li key={doc.filename}>
              <div>
                <span className="doc-name" title={doc.filename}>{doc.filename}</span>
                <span className="muted small">{doc.pages} pages</span>
              </div>
              <button className="ghost" onClick={() => onDelete(doc.filename)} aria-label={`Remove ${doc.filename}`}>
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
