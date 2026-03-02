import chromadb
import ollama

CHROMA_PATH = "chroma_db"
EMBED_MODEL = "nomic-embed-text"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="documents")


def get_embedding(text: str) -> list[float]:
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


def retrieve(query: str, n_results: int = 3) -> list[dict]:
    """Find the most semantically similar chunks to the query."""
    query_embedding = get_embedding(query)

    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append(
            {
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "chunk": results["metadatas"][0][i]["chunk"],
                "distance": results["distances"][0][i],
            }
        )

    return chunks


if __name__ == "__main__":
    query = "What is RAG and how does it work?"
    print(f"Query: {query}\n")

    results = retrieve(query)
    for i, chunk in enumerate(results):
        print(f"--- Result {i + 1} ---")
        print(f"Source  : {chunk['source']}")
        print(f"Distance: {chunk['distance']:.4f}")
        print(f"Text    : {chunk['text'][:200]}...")
        print()
