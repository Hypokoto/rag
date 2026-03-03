import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.ingestion import ingest_file, list_ingested
from core.llm import ask

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Assistant API",
    description="Local RAG pipeline powered by Ollama + ChromaDB",
    version="1.0.0"
)

# Allow requests from Streamlit and TUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response models ───────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    n_chunks: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks_used: int

class IngestResponse(BaseModel):
    success: bool
    filename: str = ""
    chunks: int = 0
    error: str = ""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "message": "RAG Assistant API is running"}


@app.get("/documents", response_model=list[str])
def get_documents():
    """List all ingested documents."""
    return list_ingested()


@app.post("/upload", response_model=IngestResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and ingest a file into the RAG pipeline."""

    # Validate file type
    allowed = [".txt", ".md", ".pdf"]
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not supported. Use: {allowed}"
        )

    # Save to uploads/
    save_path = Path("uploads") / file.filename
    save_path.write_bytes(await file.read())

    # Ingest
    result = ingest_file(str(save_path))

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return IngestResponse(
        success=True,
        filename=result["filename"],
        chunks=result["chunks"]
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """Ask a question against the RAG knowledge base."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = ask(request.question, n_chunks=request.n_chunks)

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"]
    )

def refresh_doc_list(self) -> None:
        doc_list = self.query_one("#doc-list", ListView)
        doc_list.clear()
        docs = api_documents()
        if docs:
            for doc in docs:
                doc_list.append(ListItem(Label(f"📄 {doc}")))
        else:
            doc_list.append(ListItem(Label("[dim]No documents yet[/dim]")))
