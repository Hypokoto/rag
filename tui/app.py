import sys
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Input, Button,
    Label, ListView, ListItem, Static, LoadingIndicator
)
from textual.binding import Binding
from textual import work

API_URL = "http://localhost:8000"


def api_documents() -> list[str]:
    try:
        r = requests.get(f"{API_URL}/documents")
        return r.json() if r.ok else []
    except Exception:
        return []


def api_upload(filepath: str) -> dict:
    try:
        path = Path(filepath)
        with open(path, "rb") as f:
            r = requests.post(
                f"{API_URL}/upload",
                files={"file": (path.name, f, "application/octet-stream")}
            )
        if r.ok:
            return {"success": True, **r.json()}
        return {"success": False, "error": r.json().get("detail", "Upload failed")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def api_query(question: str) -> dict:
    try:
        r = requests.post(f"{API_URL}/query", json={"question": question})
        if r.ok:
            return r.json()
        return {"answer": "API error", "sources": [], "chunks_used": 0}
    except Exception as e:
        return {"answer": f"Connection error: {e}", "sources": [], "chunks_used": 0}
