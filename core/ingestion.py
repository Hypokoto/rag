import os
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# --- Setup ---
CHROMA_PATH = "chroma_db"
UPLOAD_PATH = "uploads"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # small, fast, good quality

# Initialize ChromaDB client and collection
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="documents")

# Initialize the embedding model
embedder = SentenceTransformer(EMBED_MODEL)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # overlap keeps context between chunks

    return chunks


def ingest_file(filepath: str) -> dict:
    """Load a file, chunk it, embed it, store in ChromaDB."""
    path = Path(filepath)

    if not path.exists():
        return {"success": False, "error": f"File not found: {filepath}"}

    if path.suffix not in [".txt", ".md"]:
        return {"success": False, "error": "Only .txt and .md files supported for now"}

    # Read the file
    text = path.read_text(encoding="utf-8")

    if not text.strip():
        return {"success": False, "error": "File is empty"}

    # Chunk the text
    chunks = chunk_text(text)

    # Embed all chunks at once (faster than one by one)
    embeddings = embedder.encode(chunks).tolist()

    # Store in ChromaDB
    ids = [f"{path.stem}_chunk_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": path.name, "chunk": i} for i in range(len(chunks))],
    )

    return {"success": True, "filename": path.name, "chunks": len(chunks)}


def list_ingested() -> list[str]:
    """Return list of unique source files already in the database."""
    results = collection.get()
    sources = set()
    for meta in results["metadatas"]:
        sources.add(meta["source"])
    return list(sources)


# --- Quick test when run directly ---
if __name__ == "__main__":
    # Create a test file
    test_file = Path("uploads/test.txt")
    test_file.write_text(
        "Retrieval Augmented Generation (RAG) is a technique that combines "
        "a retrieval system with a language model. Instead of relying purely "
        "on the model's training data, RAG fetches relevant documents and "
        "includes them in the prompt. This makes answers more accurate and "
        "grounded in real information. ChromaDB is a vector database that "
        "stores embeddings and allows semantic similarity search."
    )

    print("Ingesting test file...")
    result = ingest_file("uploads/test.txt")
    print(f"Result: {result}")

    print("\nIngested files:")
    for f in list_ingested():
        print(f"  - {f}")
