"""
Persistent chat history for Hastings RAG Studio.

Stores conversations in PostgreSQL so they survive browser refreshes
and app restarts. Each conversation belongs to a knowledge base.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg

from src.db.connection import get_connection


# ── Schema ────────────────────────────────────────────────────────────────────

def init_chat_tables(conn: psycopg.Connection) -> None:
    """Create chat history tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id          SERIAL PRIMARY KEY,
            kb_id       INTEGER REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            title       VARCHAR(500),
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL
                                REFERENCES conversations(id) ON DELETE CASCADE,
            role            VARCHAR(20) NOT NULL,
            content         TEXT NOT NULL,
            sources         JSONB,
            meta            TEXT,
            created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS messages_conversation_idx
            ON messages (conversation_id);
    """)


# ── Conversations ─────────────────────────────────────────────────────────────

def create_conversation(
    conn: psycopg.Connection,
    kb_id: int,
    title: str = "New conversation",
) -> dict[str, Any]:
    """Create a new conversation and return it."""
    row = conn.execute(
        """
        INSERT INTO conversations (kb_id, title)
        VALUES (%s, %s)
        RETURNING id, kb_id, title, created_at
        """,
        (kb_id, title),
    ).fetchone()
    return dict(row)


def list_conversations(
    conn: psycopg.Connection,
    kb_id: int,
) -> list[dict[str, Any]]:
    """List all conversations for a knowledge base."""
    rows = conn.execute(
        """
        SELECT c.id, c.title, c.created_at, c.updated_at,
               COUNT(m.id) AS message_count
        FROM conversations c
        LEFT JOIN messages m ON m.conversation_id = c.id
        WHERE c.kb_id = %s
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        """,
        (kb_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def delete_conversation(conn: psycopg.Connection, conversation_id: int) -> None:
    """Delete a conversation and all its messages."""
    conn.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))


def update_conversation_title(
    conn: psycopg.Connection,
    conversation_id: int,
    title: str,
) -> None:
    """Update the title of a conversation."""
    conn.execute(
        "UPDATE conversations SET title = %s, updated_at = NOW() WHERE id = %s",
        (title, conversation_id),
    )


# ── Messages ──────────────────────────────────────────────────────────────────

def add_message(
    conn: psycopg.Connection,
    conversation_id: int,
    role: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
    meta: str | None = None,
) -> dict[str, Any]:
    """Add a message to a conversation."""
    sources_json = json.dumps(sources) if sources else None
    row = conn.execute(
        """
        INSERT INTO messages (conversation_id, role, content, sources, meta)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, conversation_id, role, content, sources, meta, created_at
        """,
        (conversation_id, role, content, sources_json, meta),
    ).fetchone()
    # Touch conversation updated_at
    conn.execute(
        "UPDATE conversations SET updated_at = NOW() WHERE id = %s",
        (conversation_id,),
    )
    return dict(row)


def get_messages(
    conn: psycopg.Connection,
    conversation_id: int,
) -> list[dict[str, Any]]:
    """Get all messages in a conversation, ordered by time."""
    rows = conn.execute(
        """
        SELECT id, role, content, sources, meta, created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conversation_id,),
    ).fetchall()
    msgs = []
    for r in rows:
        m = dict(r)
        if m.get("sources") and isinstance(m["sources"], str):
            m["sources"] = json.loads(m["sources"])
        msgs.append(m)
    return msgs


# ── Export ────────────────────────────────────────────────────────────────────

def export_conversation_markdown(
    messages: list[dict[str, Any]],
    title: str,
    kb_name: str,
) -> str:
    """Export a conversation as a Markdown string."""
    lines = [
        f"# {title}",
        f"**Knowledge base:** {kb_name}",
        "",
    ]
    for msg in messages:
        role = "**You**" if msg["role"] == "user" else "**Hastings RAG Studio**"
        lines.append(f"### {role}")
        lines.append(msg["content"])
        if msg.get("sources"):
            lines.append("")
            lines.append("*Sources:*")
            for src in msg["sources"]:
                pg = f", page {src['page_number']}" if src.get("page_number") else ""
                lines.append(f"- {src['label']} — {src['filename']}{pg}")
        lines.append("")
    return "\n".join(lines)


def export_conversation_json(
    messages: list[dict[str, Any]],
    title: str,
    kb_name: str,
) -> str:
    """Export a conversation as a JSON string."""
    data = {
        "title": title,
        "knowledge_base": kb_name,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "sources": m.get("sources") or [],
                "meta": m.get("meta") or "",
            }
            for m in messages
        ],
    }
    return json.dumps(data, indent=2)
