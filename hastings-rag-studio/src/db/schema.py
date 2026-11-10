"""
Database schema initialisation for Hastings RAG Studio.

All DDL statements are idempotent — safe to run multiple times against
an existing database. Call init_db(conn) once on startup or from the
scripts/init_db.py helper.
"""

import psycopg


def init_db(conn: psycopg.Connection) -> None:
    """
    Create the pgvector extension, all tables, and all indexes.

    This function is idempotent: running it against a database that
    already has the schema is a no-op.

    Args:
        conn: An open psycopg v3 connection. The caller is responsible
              for committing or rolling back.
    """
    from src.db.chat_history import init_chat_tables

    statements = [
        # Enable the pgvector extension
        "CREATE EXTENSION IF NOT EXISTS vector;",

        # Knowledge bases — top-level containers for documents
        """
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,

        # Documents — files uploaded into a knowledge base
        """
        CREATE TABLE IF NOT EXISTS documents (
            id           SERIAL PRIMARY KEY,
            kb_id        INTEGER NOT NULL
                             REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            filename     VARCHAR(500) NOT NULL,
            file_type    VARCHAR(50),
            content_hash VARCHAR(64),
            page_count   INTEGER,
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,

        # Chunks — text segments with embeddings
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id          SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL
                            REFERENCES documents(id) ON DELETE CASCADE,
            kb_id       INTEGER NOT NULL
                            REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content     TEXT NOT NULL,
            page_number INTEGER,
            embedding   vector(384),
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,

        # HNSW index for fast approximate nearest-neighbour search
        """
        CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx
            ON chunks
            USING hnsw (embedding vector_cosine_ops);
        """,

        # Index for fast knowledge-base-scoped lookups
        """
        CREATE INDEX IF NOT EXISTS chunks_kb_id_idx
            ON chunks (kb_id);
        """,
    ]

    for sql in statements:
        conn.execute(sql)

    # Chat history tables
    init_chat_tables(conn)
