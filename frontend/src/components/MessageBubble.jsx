export default function MessageBubble({ message }) {
  const { role, content, sources, error } = message;
  return (
    <div className={`bubble ${role} ${error ? "error" : ""}`}>
      <p dir="auto">{content}</p>
      {sources?.length > 0 && (
        <div className="sources">
          <span className="sources-title">Sources</span>
          {sources.map((s) => (
            <details key={`${s.document}-${s.page}`}>
              <summary>
                {s.document}, page {s.page}
              </summary>
              <blockquote dir="auto">{s.snippet}</blockquote>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
