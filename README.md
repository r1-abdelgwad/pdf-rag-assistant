# PDF Chatbot (RAG)

A chatbot that answers questions about your PDF documents. It keeps the conversation context,
shows which document and page each answer came from, and says so when the answer is not in the documents.

- **Backend:** Python, FastAPI
- **Frontend:** React (Vite)
- **LLM:** Groq API (`openai/gpt-oss-120b`)
- **Vector database:** ChromaDB (stored on disk)
- **Embeddings:** `intfloat/multilingual-e5-large` (English + Arabic) through the Hugging Face Inference API

## Run it

Requirements: Python 3.10+, Node.js 18+, a free [Groq API key](https://console.groq.com/keys) and a free
[Hugging Face token](https://huggingface.co/settings/tokens) (create a fine-grained token with the
"Make calls to Inference Providers" permission).

### 1. Install the backend

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

Your keys go in `backend/.env` (copy `backend/.env.example`):

```
GROQ_API_KEY=your_groq_key
HF_TOKEN=your_huggingface_token
```

### 2. Build the web interface (once)

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Run

From the project root:

```bash
python -m backend.main
```

Open http://127.0.0.1:8000 (API docs at `/docs`).

### Development mode (React hot reload)

Keep the backend running, and in another terminal:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. It forwards `/api` requests to the backend.

### Try it

Upload `sample_docs/northwind_employee_handbook.pdf` and ask:

- "How many days of annual leave do I get?" then "And after five years?" (follow-up)
- "What is the learning budget?"
- "Who won the 2018 World Cup?" (not in the document, so the bot declines)

### Tests

```bash
cd backend
pip install pytest
pytest
```

## Architecture

```
React UI ──HTTP──> FastAPI ──> RAG pipeline ──> ChromaDB (vectors on disk)
                                   ├─────────> Hugging Face (embeddings)
                                   └─────────> Groq LLM
```

```
backend/app/
  (backend/main.py      starts the server: python -m backend.main)
  app/main.py           app setup, CORS, error handling, serves the built frontend
  config.py             settings (env vars / .env)
  schemas.py            request/response models
  routes/documents.py   upload, list, delete PDFs
  routes/chat.py        chat endpoint
  services/pdf.py       text extraction + chunking
  services/embeddings.py     Hugging Face embeddings
  services/vector_store.py   ChromaDB wrapper
  services/llm.py       Groq client + prompts
  services/chat.py      the RAG pipeline
frontend/src/           App, api client, DocumentPanel, ChatWindow, MessageBubble
```

### How a question is answered

1. **Indexing:** an uploaded PDF is split into ~1000-character chunks (page by page, so each chunk
   knows its page). Chunks are embedded and stored in ChromaDB with the file name and page.
2. **Follow-ups:** if there is conversation history, the LLM first rewrites the question into a
   standalone one ("And after five years?" becomes "How many days of annual leave after five years of service?"),
   so retrieval works for follow-ups.
3. **Retrieval:** the top 4 chunks are fetched by cosine similarity. Chunks that are not similar
   enough (`MAX_DISTANCE`) are dropped.
4. **Grounded answer:** the LLM gets only those chunks and strict rules: answer from the context,
   otherwise reply with a fixed "not found" sentence. Temperature is low (0.2).
5. **Sources:** the response includes the document name, page and an excerpt for every chunk used.
   When the bot answers "not found" or has no relevant chunks, no sources are shown.

### Decisions

- **Stateless backend:** the frontend sends the recent messages with each request. This keeps the
  server simple and means a restart never loses or mixes up conversations.
- **No LangChain:** the pipeline is ~60 lines of plain Python, easier to read, test and explain.
- **ChromaDB:** a real vector database with persistence and metadata filtering, no server to run.
- **Groq:** fast and free tier available. Swapping the provider only means changing `services/llm.py`.

### Error handling

Invalid Hugging Face token, embedding model not available, rate limits,
invalid or oversized files, non-PDF uploads, password-protected or scanned PDFs (no text),
empty questions, missing or invalid API key, LLM rate limits and network failures all return a
clear message that the UI shows to the user. Re-uploading a file replaces the old version.

### Limitations

- Scanned PDFs need OCR, which is not included.
- The model must be served by the Hugging Face `hf-inference` provider. Each embedding model gets its own collection, so after changing `EMBEDDING_MODEL` you need to upload your PDFs again. Models that do not use e5-style prefixes need `EMBEDDING_QUERY_PREFIX=` and `EMBEDDING_DOCUMENT_PREFIX=` set to empty.
- Document text is sent to the Hugging Face API to be embedded, so do not upload confidential files.
- All users share one knowledge base (no authentication).
- Tune `MAX_DISTANCE` in `.env` if the bot refuses too often (raise it) or answers off-topic questions (lower it).
