import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import requests

API_URL = "http://localhost:8000"

# --- Page config ---
st.set_page_config(
    page_title="RAG Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS --- (keep exactly the same as before)
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stChatMessage { border-radius: 12px; margin-bottom: 0.5rem; }
    .source-badge {
        display: inline-block;
        background: #2D1B69;
        color: #A78BFA;
        border: 1px solid #7C3AED;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        margin: 2px;
        font-family: monospace;
    }
    .doc-card {
        background: #1A1A2E;
        border: 1px solid #2D2D4E;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
    .section-header {
        color: #7C3AED;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .preview-box {
        background: #0F0F1A;
        border: 1px solid #2D2D4E;
        border-left: 3px solid #7C3AED;
        border-radius: 4px;
        padding: 0.75rem;
        font-size: 0.8rem;
        font-family: monospace;
        color: #94A3B8;
        white-space: pre-wrap;
        max-height: 200px;
        overflow-y: auto;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- API helpers ---
def api_upload(file) -> dict:
    response = requests.post(
        f"{API_URL}/upload",
        files={"file": (file.name, file.getvalue(), file.type)}
    )
    if response.ok:
        return {"success": True, **response.json()}
    return {"success": False, "error": response.json().get("detail", "Unknown error")}


def api_query(question: str) -> dict:
    response = requests.post(
        f"{API_URL}/query",
        json={"question": question}
    )
    if response.ok:
        return response.json()
    return {"answer": "API error", "sources": [], "chunks_used": 0}


def api_documents() -> list[str]:
    response = requests.get(f"{API_URL}/documents")
    return response.json() if response.ok else []


# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
if "preview_text" not in st.session_state:
    st.session_state.preview_text = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 RAG Assistant")
    st.markdown("---")

    st.markdown('<p class="section-header">📤 Upload Document</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["txt", "md", "pdf"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None and uploaded_file.name != st.session_state.last_uploaded:
        with st.spinner(f"Ingesting {uploaded_file.name}..."):
            result = api_upload(uploaded_file)

        if result["success"]:
            st.success(f"✅ {result['filename']} — {result['chunks']} chunks")
            st.session_state.last_uploaded = uploaded_file.name
            if uploaded_file.type == "text/plain" or uploaded_file.name.endswith(".md"):
                st.session_state.preview_text = uploaded_file.getvalue().decode("utf-8")[:800]
            else:
                st.session_state.preview_text = f"📄 PDF ingested: {uploaded_file.name}\n({result['chunks']} chunks extracted)"
        else:
            st.error(f"❌ {result['error']}")

    if st.session_state.preview_text:
        st.markdown("---")
        st.markdown('<p class="section-header">👁 Document Preview</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="preview-box">{st.session_state.preview_text}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown('<p class="section-header">📚 Knowledge Base</p>', unsafe_allow_html=True)
    for f in api_documents():
        st.markdown(f'<div class="doc-card">📄 {f}</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Main chat area ────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    st.markdown("### 💬 Ask Your Documents")
    st.markdown("---")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                sources_html = "".join(
                    f'<span class="source-badge">📄 {s}</span>'
                    for s in msg["sources"]
                )
                st.markdown(sources_html, unsafe_allow_html=True)

    if query := st.chat_input("Ask a question about your documents..."):
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = api_query(query)
            st.markdown(result["answer"])
            sources_html = "".join(
                f'<span class="source-badge">📄 {s}</span>'
                for s in result["sources"]
            )
            st.markdown(sources_html, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"]
        })
