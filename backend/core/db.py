"""Embedded SQLite database layer for LocalMind: persistent conversations, messages, and long-term memories."""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "localmind.db"


def get_db_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a thread-safe connection to the SQLite database with WAL mode."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH):
    """Initialize database tables and indices."""
    with get_db_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                model_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_memories (
                id TEXT PRIMARY KEY,
                fact TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
        """)


# =====================================================================
# CONVERSATIONS
# =====================================================================

def create_or_update_conversation(conv_id: str, title: str, model_name: Optional[str] = None, db_path: Path = DEFAULT_DB_PATH):
    """Insert or update a conversation session."""
    now = datetime.utcnow().isoformat()
    with get_db_connection(db_path) as conn:
        existing = conn.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE conversations SET title = ?, model_name = coalesce(?, model_name), updated_at = ? WHERE id = ?",
                (title, model_name, now, conv_id)
            )
        else:
            conn.execute(
                "INSERT INTO conversations (id, title, model_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, model_name, now, now)
            )


def get_all_conversations(db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all conversations ordered by most recent."""
    with get_db_connection(db_path) as conn:
        rows = conn.execute("SELECT id, title, model_name, updated_at FROM conversations ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def get_conversation_messages(conv_id: str, db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all messages for a specific conversation in chronological order."""
    with get_db_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def save_message(conv_id: str, role: str, content: str, db_path: Path = DEFAULT_DB_PATH) -> str:
    """Save an individual message turn to the database."""
    msg_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_db_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg_id, conv_id, role, content, now)
        )
        # Update conversation timestamp
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
    return msg_id


def delete_conversation_by_id(conv_id: str, db_path: Path = DEFAULT_DB_PATH) -> bool:
    """Delete a conversation and its cascaded messages."""
    with get_db_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        return cur.rowcount > 0


# =====================================================================
# PERSISTENT CROSS-SESSION MEMORIES (FRONTIER MEMORY)
# =====================================================================

def get_all_memories(db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all long-term persistent user memories."""
    with get_db_connection(db_path) as conn:
        rows = conn.execute("SELECT id, fact, category, created_at FROM user_memories ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_user_memory(fact: str, category: str = "general", db_path: Path = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Store a new long-term persistent user memory."""
    mem_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_db_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO user_memories (id, fact, category, created_at) VALUES (?, ?, ?, ?)",
            (mem_id, fact.strip(), category, now)
        )
    return {"id": mem_id, "fact": fact.strip(), "category": category, "created_at": now}


def delete_user_memory(mem_id: str, db_path: Path = DEFAULT_DB_PATH) -> bool:
    """Delete a long-term persistent user memory by id."""
    with get_db_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM user_memories WHERE id = ?", (mem_id,))
        return cur.rowcount > 0
