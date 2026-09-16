![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

<div align="center">

RAG Chatbot – Ask Questions From Your PDFs



Upload a PDF, ask questions in plain English, and get answers based on your document.

</div>
---

## What can you do with it?

1. Upload a PDF (resume, report, notes, paper, manual).
2. Ask a question like “Summarize the key findings” or “What is the main topic?”
3. Get a short, focused answer based only on that PDF.

No API key needed. Everything runs locally on your machine.

**Example:**

> PDF uploaded: `internship-report.pdf`
> You ask: “What are the important concepts?”
> Bot answers: from the report content only. If the answer is not in the PDF, it says so clearly instead of guessing.

---

## How it works (in 4 steps)

1. **Read PDF** – Extracts text and splits it into small chunks (1000 chars with 200 overlap so context is not lost).
2. **Understand meaning** – Converts each chunk into a number (embedding) that captures its meaning.
3. **Find relevant parts** – When you ask a question, finds the top 3 most similar chunks using FAISS (fast similarity search).
4. **Write answer** – Gives those 3 chunks + your question to a small AI model (FLAN-T5) which writes the final answer.

```
PDF → Chunks → Embeddings → FAISS → Top 3 chunks + Question → FLAN-T5 → Answer
```

---

## Key Features

- PDF upload and automatic processing
- Answers grounded in your document, not AI memory
- Says “not found in document” instead of hallucinating
- Simple chat UI with light/dark mode, chat history, and file attach
- Runs fully offline with free, open-source models
- FastAPI backend with auto docs at `/docs`

---

## Tech Stack

| What it does | Tool used |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| AI flow | LangChain |
| Search database | FAISS (in-memory vector search) |
| Understands text meaning | `sentence-transformers/all-MiniLM-L6-v2` |
| Writes answers | `google/flan-t5-small` via HuggingFace |
| Reads PDFs | PyPDF |
| Frontend | HTML, CSS, JavaScript (no build step) |

Why these models? Both are small, free, and run on CPU. No GPU or paid API needed. Good for learning and demos.

---

## Project Structure

```
RAG-ChatBot/
├── Backend/
│   ├── app.py            # API: /upload PDF, /ask question
│   └── requirements.txt  # Python dependencies
├── Frontend/
│   ├── index.html        # Chat UI
│   ├── script.js         # Upload + chat logic
│   └── styles.css        # Styling
├── README.md
└── LICENSE
```

You don’t need to open the code to use it. This structure is only if you want to explore or modify it.

---

## How to run locally

**You need:** Python 3.10+, a browser.

**1. Clone and install:**

```bash
git clone https://github.com/Mohak-talodhikar/RAG-ChatBot.git
cd RAG-ChatBot
pip install -r Backend/requirements.txt
```

**2. Start backend:**

```bash
cd Backend
uvicorn app:app --reload
```

Open: `http://127.0.0.1:8000/docs` to see the API.

**3. Start frontend (new terminal):**

```bash
cd Frontend
python -m http.server 3000
```

Open: `http://localhost:3000`

---

## How to use

1. Open the frontend in your browser.
2. Click attach icon, select a PDF, wait for “processed successfully”.
3. Type your question, press Enter.
4. To try another document, just upload a new PDF (it replaces the old one).

Two main APIs (if you are technical):

- `POST /upload` – send PDF file, it gets processed and indexed.
- `POST /ask` – send `{"query": "your question"}`, get `{"answer": "..."}` back.

---

## Limitations (honest note)

- Only 1 PDF at a time per conversation.
- Chat history is saved in SQLite (`chats.db`) and survives restarts.
- Best for short, factual questions. Long answers are capped at ~512 tokens.
- CPU-based, so large PDFs take some time.
- No login / no multi-user support yet.

---

## What I learned from this project

- Building an end-to-end RAG pipeline (load → chunk → embed → retrieve → generate)
- Semantic search with FAISS and embeddings
- Prompt design to reduce hallucination (“say if not in context”)
- Cleaning LLM output (remove repeats and artifacts)
- Backend development with FastAPI + connecting to a plain JS frontend

---

## Author

**Mohak Talodhikar**

- [LinkedIn](https://www.linkedin.com/in/mohak-talodhikar/)
- [GitHub](https://github.com/mohaktalodhikar)
- [Instagram](https://www.instagram.com/mohak_talodhikar/)