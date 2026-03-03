import ollama
from retrieval import retrieve

LLM_MODEL = "mistral"


def ask(query: str, n_chunks: int = 3) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks from ChromaDB
    2. Build a prompt with those chunks as context
    3. Ask Mistral to answer using that context
    """

    # Step 1 — Retrieve
    chunks = retrieve(query, n_results=n_chunks)

    if not chunks:
        return {
            "answer": "I don't have any documents to answer from. Please upload a file first.",
            "sources": [],
        }

    # Step 2 — Build context string from retrieved chunks
    context = "\n\n".join(
        [f"[Source: {c['source']}, chunk {c['chunk']}]\n{c['text']}" for c in chunks]
    )

    # Step 3 — Build the prompt
    prompt = f"""You are a helpful assistant. Answer the user's question using ONLY
the context provided below. If the answer is not in the context, say so clearly.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""

    # Step 4 — Call Mistral via Ollama
    response = ollama.chat(
        model=LLM_MODEL, messages=[{"role": "user", "content": prompt}]
    )

    answer = response["message"]["content"]
    sources = list(set(c["source"] for c in chunks))

    return {"answer": answer, "sources": sources, "chunks_used": len(chunks)}


if __name__ == "__main__":
    questions = [
        "What is RAG and how does it work?",
        "What is ChromaDB used for?",
        "What is the capital of France?",  # not in docs — should say so
    ]

    for q in questions:
        print(f"\n{'=' * 50}")
        print(f"Q: {q}")
        result = ask(q)
        print(f"A: {result['answer']}")
        print(f"Sources: {result['sources']}")
