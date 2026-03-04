# 🧠 RAG Assistant

A fully local Retrieval-Augmented Generation (RAG) system built with Python.
Ask questions about your documents — no cloud, no API costs, no data leaving your machine.

## Architecture
```
rag-project/
├── core/          # RAG brain (ingestion, retrieval, LLM)
├── api/           # FastAPI backend (shared by all interfaces)
├── webapp/        # Streamlit browser UI
├── tui/           # Textual terminal UI
└── uploads/       # Drop files here to ingest
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Ollama (Mistral) |
| Embeddings | Ollama (nomic-embed-text) |
| Vector DB | ChromaDB |
| Backend API | FastAPI |
| Web UI | Streamlit |
| Terminal UI | Textual |

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- Ollama models: `mistral` and `nomic-embed-text`
```bash
ollama pull mistral
ollama pull nomic-embed-text
```

## Setup
```bash
# Clone the repo
git clone https://github.com/hypokoto/rag-project.git
cd rag-project

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

You need three terminals:

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — API backend:**
```bash
uvicorn api.main:app --reload --port 8000
```

**Terminal 3 — Choose your interface:**
```bash
# Browser UI
streamlit run webapp/app.py

# Terminal UI
python3 tui/app.py
```

## Usage

1. Upload a `.txt`, `.md`, or `.pdf` file via the webapp sidebar or TUI upload panel
2. Ask questions about the document in the chat
3. The system retrieves relevant chunks and answers using your local LLM

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/documents` | List ingested documents |
| POST | `/upload` | Upload and ingest a file |
| POST | `/query` | Ask a question |

Interactive API docs available at `http://localhost:8000/docs`

## Roadmap

- [ ] Gemini web search integration
- [ ] Streaming responses
- [ ] MCP (Model Context Protocol) support
- [ ] Multi-user authentication
