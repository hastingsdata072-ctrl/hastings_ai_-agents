"""
Database initialisation script for Hastings RAG Studio.

Run this once before starting the application:

    python scripts/init_db.py

Safe to run multiple times — all DDL is idempotent.
"""

import sys
import os

# Make sure the project root is on the path when running from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.connection import get_connection
from src.db.schema import init_db


def main() -> None:
    print("Initialising Hastings RAG Studio database…")
    try:
        # First pass: create the extension without registering the vector type
        # (the type doesn't exist yet, so register_vector would fail)
        with get_connection(register_vector_type=False) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Second pass: now the extension exists, register vector and create tables
        with get_connection() as conn:
            init_db(conn)
        print("✅ Database initialised successfully.")
        print("   Tables created: knowledge_bases, documents, chunks")
        print("   Indexes created: HNSW embedding index, kb_id index")
    except Exception as exc:
        print(f"❌ Initialisation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
