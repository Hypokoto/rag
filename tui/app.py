import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Input, Button,
    Label, ListView, ListItem, Static, LoadingIndicator
)
from textual.binding import Binding
from textual import work

from core.ingestion import ingest_file, list_ingested
from core.llm import ask


# ── Small reusable widgets ────────────────────────────────────────────────────

class ChatMessage(Static):
    """A single chat bubble."""

    def __init__(self, role: str, content: str, sources: list[str] = []):
        prefix = "🧑 You" if role == "user" else "🤖 Assistant"
        sources_line = ""
        if sources:
            sources_line = f"\n[dim]📄 {', '.join(sources)}[/dim]"
        super().__init__(f"[bold]{prefix}[/bold]\n{content}{sources_line}")
        self.add_class(role)  # adds CSS class "user" or "assistant"


# ── Main App ──────────────────────────────────────────────────────────────────

class RAGApp(App):
    """RAG Assistant TUI."""

    CSS = """
    Screen {
        background: #0f0f0f;
    }

    /* ── Layout ── */
    #main {
        height: 1fr;
    }

    #sidebar {
        width: 30;
        background: #1a1a2e;
        border-right: solid #2d2d4e;
        padding: 1;
    }

    #chat-area {
        width: 1fr;
        padding: 1 2;
    }

    /* ── Sidebar ── */
    #sidebar-title {
        color: #7c3aed;
        text-style: bold;
        margin-bottom: 1;
    }

    #section-label-kb, #section-label-upload {
    color: #7c3aed;
    text-style: bold;
    margin-top: 1;
    margin-bottom: 0;
}

    #doc-list {
        height: auto;
        max-height: 12;
        background: #0f0f1a;
        border: solid #2d2d4e;
        margin-bottom: 1;
    }

    ListItem {
        padding: 0 1;
        color: #94a3b8;
    }

    ListItem:hover {
        background: #2d1b69;
        color: #e2e8f0;
    }

    #upload-input {
        margin-bottom: 1;
        border: solid #2d2d4e;
    }

    #upload-input:focus {
        border: solid #7c3aed;
    }

    #upload-btn {
        width: 1fr;
        background: #2d1b69;
        color: #a78bfa;
        border: solid #7c3aed;
    }

    #upload-btn:hover {
        background: #7c3aed;
        color: #ffffff;
    }

    #upload-status {
        color: #64748b;
        height: 2;
        margin-top: 1;
    }

    /* ── Chat ── */
    #messages {
        height: 1fr;
        border: solid #2d2d4e;
        background: #0f0f1a;
        padding: 1;
        margin-bottom: 1;
    }

    ChatMessage {
        margin-bottom: 1;
        padding: 1;
        border-left: solid #2d2d4e;
    }

    ChatMessage.user {
        border-left: solid #7c3aed;
        background: #1a1a2e;
    }

    ChatMessage.assistant {
        border-left: solid #0ea5e9;
        background: #0f1a2e;
    }

    #input-row {
        height: 3;
        margin-top: 1;
    }

    #query-input {
        width: 1fr;
        border: solid #2d2d4e;
    }

    #query-input:focus {
        border: solid #7c3aed;
    }

    #send-btn {
        width: 10;
        background: #2d1b69;
        color: #a78bfa;
        border: solid #7c3aed;
        margin-left: 1;
    }

    #send-btn:hover {
        background: #7c3aed;
        color: #ffffff;
    }

    #loading {
        height: 1;
        display: none;
        color: #7c3aed;
    }

    #loading.visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear Chat"),
        Binding("f1", "focus_upload", "Upload"),
        Binding("f2", "focus_query", "Query"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main"):

            # ── Sidebar ──────────────────────────────────────
            with Vertical(id="sidebar"):
                yield Label("🧠 RAG Assistant", id="sidebar-title")
                yield Label("📚 KNOWLEDGE BASE", id="section-label-kb")
                yield ListView(id="doc-list")

                yield Label("📤 UPLOAD FILE", id="section-label-upload")
                yield Input(placeholder="Path to file...", id="upload-input")
                yield Button("Upload", id="upload-btn")
                yield Label("", id="upload-status")

            # ── Chat area ─────────────────────────────────────
            with Vertical(id="chat-area"):
                yield ScrollableContainer(id="messages")
                yield LoadingIndicator(id="loading")

                with Horizontal(id="input-row"):
                    yield Input(placeholder="Ask a question...", id="query-input")
                    yield Button("Send", id="send-btn")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts — load existing documents."""
        self.refresh_doc_list()
        self.query_one("#query-input").focus()

    def refresh_doc_list(self) -> None:
        """Reload the knowledge base list in the sidebar."""
        doc_list = self.query_one("#doc-list", ListView)
        doc_list.clear()
        docs = list_ingested()
        if docs:
            for doc in docs:
                doc_list.append(ListItem(Label(f"📄 {doc}")))
        else:
            doc_list.append(ListItem(Label("[dim]No documents yet[/dim]")))

    def add_message(self, role: str, content: str, sources: list[str] = []) -> None:
        """Add a chat bubble to the messages area."""
        messages = self.query_one("#messages", ScrollableContainer)
        msg = ChatMessage(role, content, sources)
        messages.mount(msg)
        messages.scroll_end(animate=False)

    # ── Button clicks ─────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "upload-btn":
            self.handle_upload()
        elif event.button.id == "send-btn":
            self.handle_query()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Allow pressing Enter in either input."""
        if event.input.id == "upload-input":
            self.handle_upload()
        elif event.input.id == "query-input":
            self.handle_query()

    # ── Upload ────────────────────────────────────────────────────────────────

    def handle_upload(self) -> None:
        upload_input = self.query_one("#upload-input", Input)
        status = self.query_one("#upload-status", Label)
        filepath = upload_input.value.strip()

        if not filepath:
            status.update("[yellow]Please enter a file path[/yellow]")
            return

        status.update("[dim]Ingesting...[/dim]")
        result = ingest_file(filepath)

        if result["success"]:
            status.update(
                f"[green]✅ {result['filename']}\n{result['chunks']} chunks[/green]"
            )
            upload_input.value = ""
            self.refresh_doc_list()
        else:
            status.update(f"[red]❌ {result['error']}[/red]")

    # ── Query (runs in background thread so UI doesn't freeze) ───────────────

    @work(thread=True)
    def handle_query(self) -> None:
        query_input = self.query_one("#query-input", Input)
        query = query_input.value.strip()

        if not query:
            return

        # Clear input and show user message
        self.call_from_thread(query_input.__setattr__, "value", "")
        self.call_from_thread(self.add_message, "user", query)

        # Show loading
        loading = self.query_one("#loading")
        self.call_from_thread(loading.add_class, "visible")

        # Run RAG pipeline (this is the slow part)
        result = ask(query)

        # Hide loading and show answer
        self.call_from_thread(loading.remove_class, "visible")
        self.call_from_thread(
            self.add_message,
            "assistant",
            result["answer"],
            result["sources"]
        )

    # ── Key actions ───────────────────────────────────────────────────────────

    def action_clear_chat(self) -> None:
        messages = self.query_one("#messages", ScrollableContainer)
        messages.remove_children()

    def action_focus_upload(self) -> None:
        self.query_one("#upload-input").focus()

    def action_focus_query(self) -> None:
        self.query_one("#query-input").focus()


if __name__ == "__main__":
    app = RAGApp()
    app.run()
