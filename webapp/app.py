import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from core.ingestion import ingest_file, list_ingested
from core.llm import ask

# --- Page config ---
st.set_page_config(
    page_title="RAG Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Chat messages */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }

    /* Source badge */
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

    /* Document card */
    .doc-card {
        background: #1A1A2E;
        border: 1px solid #2D2D4E;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }

    /* Section headers */
    .section-header {
        color: #7C3AED;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    /* Preview box */
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

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
if "preview_text" not in st.session_state:
    st.session_state.preview_text = None

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🧠 RAG Assistant")
    st.markdown("---")

    # --- Upload ---
    st.markdown('<p class="section-header">📤 Upload Document</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["txt", "md", "pdf"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None and uploaded_file.name != st.session_state.last_uploaded:
        save_path = Path("uploads") / uploaded_file.name
        save_path.write_bytes(uploaded_file.getvalue())

        with st.spinner(f"Ingesting {uploaded_file.name}..."):
            result = ingest_file(str(save_path))

        if result["success"]:
            st.success(f"✅ {result['filename']} — {result['chunks']} chunks")
            st.session_state.last_uploaded = uploaded_file.name

            # Generate preview
            if uploaded_file.type == "text/plain" or uploaded_file.name.endswith(".md"):
                raw = uploaded_file.getvalue().decode("utf-8")
                st.session_state.preview_text = raw[:800]
            else:
                st.session_state.preview_text = f"📄 PDF ingested: {uploaded_file.name}\n({result['chunks']} chunks extracted and stored)"
        else:
            st.error(f"❌ {result['error']}")

    # --- Document preview ---
    if st.session_state.preview_text:
        st.markdown("---")
        st.markdown('<p class="section-header">👁 Document Preview</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="preview-box">{st.session_state.preview_text}</div>',
            unsafe_allow_html=True
        )

    # --- Knowledge base ---
    st.markdown("---")
    st.markdown('<p class="section-header">📚 Knowledge Base</p>', unsafe_allow_html=True)

    ingested = list_ingested()
    if ingested:
        for f in ingested:
            st.markdown(f'<div class="doc-card">📄 {f}</div>', unsafe_allow_html=True)
    else:
        st.caption("No documents yet.")

    # --- Clear chat ---
    st.markdown("---")
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# MAIN AREA — Chat
# ============================================================
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    st.markdown("### 💬 Ask Your Documents")
    st.markdown("---")

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                sources_html = "".join(
                    f'<span class="source-badge">📄 {s}</span>'
                    for s in msg["sources"]
                )
                st.markdown(sources_html, unsafe_allow_html=True)

    # Chat input
    if query := st.chat_input("Ask a question about your documents..."):
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = ask(query)
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
