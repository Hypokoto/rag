import chromadb
from sentence_transformers import SentenceTransformer

# --- Same setup as ingestion (same database) ---
CHROMA_PATH = "chroma_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="documents")
embedder = SentenceTransformer(EMBED_MODEL)


def retrieve(query: str, n_results: int = 3) -> list[dict]:
    """Find the most semantically similar chunks to the query."""

    # Embed the query using the same model used during ingestion
    query_embedding = embedder.encode(query).tolist()

    # Ask ChromaDB for the closest matching chunks
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    # Package results into a clean list of dicts
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append(
            {
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "chunk": results["metadatas"][0][i]["chunk"],
                "distance": results["distances"][0][i],  # lower = more similar
            }
        )

    return chunks


if __name__ == "__main__":
    query = "What is RAG and how does it work?"
    print(f"Query: {query}\n")

    results = retrieve(query)

    for i, chunk in enumerate(results):
        print(f"--- Result {i + 1} ---")
        print(f"Source : {chunk['source']}")
        print(f"Distance: {chunk['distance']:.4f}  (lower = more relevant)")
        print(f"Text   : {chunk['text'][:200]}...")
        print()
