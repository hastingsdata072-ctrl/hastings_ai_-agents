"""
Milestone 1 acceptance test — database connection and schema.

Run with:
    python tests/test_db_connection.py

Prints PASS or FAIL for each check. Exits with code 1 if any check fails.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.connection import get_connection

PASS = "PASS ✅"
FAIL = "FAIL ❌"

results: list[tuple[str, bool]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    tag = PASS if ok else FAIL
    suffix = f"  →  {detail}" if detail else ""
    print(f"  [{tag}] {label}{suffix}")
    results.append((label, ok))


def main() -> None:
    print("\n═══════════════════════════════════════════")
    print("  Hastings RAG Studio — DB Acceptance Test")
    print("═══════════════════════════════════════════\n")

    try:
        with get_connection() as conn:

            # ── Check 1: PostgreSQL version ───────────────────────────────
            row = conn.execute("SELECT version() AS v").fetchone()
            version = row["v"] if row else ""
            check("PostgreSQL connection", bool(version), version)

            # ── Check 2: pgvector available ───────────────────────────────
            avail = conn.execute(
                "SELECT default_version FROM pg_available_extensions "
                "WHERE name = 'vector';"
            ).fetchone()
            check(
                "pgvector available in build",
                avail is not None,
                f"version {avail['default_version']}" if avail else "NOT FOUND",
            )

            # ── Check 3: pgvector extension active ────────────────────────
            active = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
            ).fetchone()
            check(
                "pgvector extension enabled",
                active is not None,
                f"active version {active['extversion']}" if active else "NOT ENABLED — run init_db",
            )

            # ── Check 4: Tables exist ─────────────────────────────────────
            for table in ("knowledge_bases", "documents", "chunks"):
                row = conn.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = %s;",
                    (table,),
                ).fetchone()
                check(f"Table '{table}' exists", row is not None)

            # ── Check 5: HNSW index exists ────────────────────────────────
            idx = conn.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'chunks' AND indexname = 'chunks_embedding_hnsw_idx';"
            ).fetchone()
            check("HNSW index on chunks.embedding", idx is not None)

    except Exception as exc:
        print(f"\n  [FAIL ❌] Could not connect to the database: {exc}\n")
        sys.exit(1)

    # ── Summary ───────────────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for _, ok in results if ok)
    failed = total - passed

    print(f"\n{'─'*45}")
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} FAILED)")
        sys.exit(1)
    else:
        print("  — all good!")
    print(f"{'─'*45}\n")


if __name__ == "__main__":
    main()
