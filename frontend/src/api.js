// Thin wrapper around the backend API. Every function throws an Error with a
// readable message, so the UI can show it directly.
const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map((d) => d.msg).join(", ");
    } catch {
      /* response had no JSON body */
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

export const getHealth = () => request("/health");
export const listDocuments = () => request("/documents");

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form });
}

export const deleteDocument = (filename) =>
  request(`/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });

export const sendChat = (message, history) =>
  request("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
