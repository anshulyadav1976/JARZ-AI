"""SQLite persistence for chat conversations and messages."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# DB file next to backend app (e.g. backend/app/chat.db)
DB_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("CHAT_DB_PATH", str(DB_DIR / "chat.db"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create conversations and messages tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                a2ui_snapshot TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)"
        )
        conn.commit()
    finally:
        conn.close()


def create_conversation(title: Optional[str] = None) -> str:
    """Create a new conversation; returns conversation id."""
    conn = _get_conn()
    try:
        cid = str(uuid.uuid4())
        now = _utc_now()
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (cid, title or "New chat", now, now),
        )
        conn.commit()
        return cid
    finally:
        conn.close()


def update_conversation_updated_at(conversation_id: str) -> None:
    """Update conversation's updated_at timestamp."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_utc_now(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def add_message(
    conversation_id: str,
    role: str,
    content: Optional[str] = None,
    a2ui_snapshot: Optional[list] = None,
) -> str:
    """Append a message to a conversation. Returns message id."""
    conn = _get_conn()
    try:
        mid = str(uuid.uuid4())
        now = _utc_now()
        a2ui_json = json.dumps(a2ui_snapshot) if a2ui_snapshot else None
        conn.execute(
            """INSERT INTO messages (id, conversation_id, role, content, a2ui_snapshot, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (mid, conversation_id, role, content or "", a2ui_json, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        return mid
    finally:
        conn.close()


def get_conversations(limit: int = 50) -> list[dict]:
    """List conversations, most recently updated first."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT id, title, created_at, updated_at
               FROM conversations ORDER BY updated_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_conversation_with_messages(conversation_id: str) -> Optional[dict]:
    """Get one conversation with all messages in order."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        if not row:
            return None
        msg_rows = conn.execute(
            """SELECT id, role, content, a2ui_snapshot, created_at
               FROM messages WHERE conversation_id = ? ORDER BY created_at ASC""",
            (conversation_id,),
        ).fetchall()
        messages = []
        for r in msg_rows:
            a2ui = None
            if r["a2ui_snapshot"]:
                try:
                    a2ui = json.loads(r["a2ui_snapshot"])
                except (json.JSONDecodeError, TypeError):
                    pass
            messages.append({
                "id": r["id"],
                "role": r["role"],
                "content": r["content"] or "",
                "a2ui_snapshot": a2ui,
                "created_at": r["created_at"],
            })
        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": messages,
        }
    finally:
        conn.close()


def set_conversation_title(conversation_id: str, title: str) -> None:
    """Set conversation title (e.g. first user message preview)."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title[:200] if title else "New chat", _utc_now(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()
