"""SQLite-backed canonical ORA retrieval index."""

from __future__ import annotations

import json
from contextlib import closing
import re
import sqlite3
from pathlib import Path
from typing import Any

from .chunker import chunk_text
from .hashing import sha256_text
from .manifest import CORE_SCOPE, load_source_manifest, read_uri

TOKEN_RE = re.compile(r"[A-Za-z0-9_+.-]+")


class IndexError(ValueError):
    """Raised when indexing violates ORA_CORE_RAG policy."""


class ORACoreIndex:
    """Local SQLite FTS5 index for ORA core documents."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with closing(self.connect()) as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    source_id TEXT PRIMARY KEY,
                    uri TEXT NOT NULL,
                    title TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    canon_level TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES documents(source_id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    heading TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    chunk_hash TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
                    chunk_id UNINDEXED,
                    source_id UNINDEXED,
                    title UNINDEXED,
                    text
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS route_manifests (
                    route_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    manifest_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_document(self, source: dict[str, Any], text: str) -> dict[str, Any]:
        source_id = str(source.get("id", "")).strip()
        scope = str(source.get("scope", "")).strip()
        if scope != CORE_SCOPE:
            raise IndexError(f"Refusing to index non-ORA_CORE source {source_id!r} with scope {scope!r}.")
        if not source_id:
            raise IndexError("Source id is required.")

        self.initialize()
        title = str(source.get("title") or source_id)
        kind = str(source.get("kind") or "unknown")
        uri = str(source.get("uri") or "")
        canon_level = str(source.get("canon_level") or "CORE")
        tags = list(source.get("tags") or [])
        source_hash = sha256_text(text)
        chunks = chunk_text(text, kind=kind)

        with closing(self.connect()) as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.execute("DELETE FROM chunk_fts WHERE source_id = ?", (source_id,))
            db.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
            db.execute(
                """
                INSERT INTO documents (source_id, uri, title, kind, scope, canon_level, tags_json, source_hash, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (source_id, uri, title, kind, scope, canon_level, json.dumps(tags), source_hash, len(text)),
            )

            for chunk in chunks:
                chunk_hash = sha256_text(f"{source_id}\n{chunk.index}\n{chunk.heading}\n{chunk.text}")
                chunk_id = chunk_hash[:32]
                metadata = {
                    "heading": chunk.heading,
                    "canon_level": canon_level,
                    "tags": tags,
                    "source_hash": source_hash,
                }
                db.execute(
                    """
                    INSERT INTO chunks (chunk_id, source_id, chunk_index, heading, text, metadata_json, chunk_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, source_id, chunk.index, chunk.heading, chunk.text, json.dumps(metadata, sort_keys=True), chunk_hash),
                )
                db.execute(
                    "INSERT INTO chunk_fts (chunk_id, source_id, title, text) VALUES (?, ?, ?, ?)",
                    (chunk_id, source_id, title, chunk.text),
                )


            db.commit()

        return {"source_id": source_id, "chunk_count": len(chunks), "source_hash": source_hash}

    def ingest_manifest(self, manifest_path: str | Path) -> list[dict[str, Any]]:
        manifest_path = Path(manifest_path)
        sources = load_source_manifest(manifest_path)
        results = []
        for source in sources:
            text = read_uri(str(source["uri"]), base_dir=manifest_path.parent)
            results.append(self.add_document(source, text))
        return results

    def query(self, query: str, *, top_k: int = 5) -> dict[str, Any]:
        self.initialize()
        normalized_query = self._normalize_query(query)
        if not normalized_query:
            return self._packet(query=query, status="UNSURE", results=[])

        with closing(self.connect()) as db:
            try:
                rows = db.execute(
                    """
                    SELECT c.chunk_id, c.source_id, d.title, d.uri, c.heading, c.text, c.metadata_json,
                           bm25(chunk_fts) AS score
                    FROM chunk_fts
                    JOIN chunks c ON c.chunk_id = chunk_fts.chunk_id
                    JOIN documents d ON d.source_id = c.source_id
                    WHERE chunk_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (normalized_query, top_k),
                ).fetchall()
            except sqlite3.Error:
                rows = self._query_like(db, normalized_query, top_k)

        results = [self._row_to_result(row) for row in rows]
        status = "SUPPORTED" if results else "UNSURE"
        return self._packet(query=query, status=status, results=results)

    def _query_like(self, db: sqlite3.Connection, query: str, top_k: int) -> list[sqlite3.Row]:
        terms = TOKEN_RE.findall(query)
        if not terms:
            return []
        where = " AND ".join(["c.text LIKE ?" for _ in terms])
        params = [f"%{term}%" for term in terms]
        params.append(top_k)
        return db.execute(
            f"""
            SELECT c.chunk_id, c.source_id, d.title, d.uri, c.heading, c.text, c.metadata_json,
                   0.0 AS score
            FROM chunks c
            JOIN documents d ON d.source_id = c.source_id
            WHERE {where}
            LIMIT ?
            """,
            params,
        ).fetchall()

    def _row_to_result(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "chunk_id": row["chunk_id"],
            "source_id": row["source_id"],
            "title": row["title"],
            "uri": row["uri"],
            "heading": row["heading"],
            "score": row["score"],
            "text": row["text"],
            "metadata": json.loads(row["metadata_json"]),
        }

    def _packet(self, *, query: str, status: str, results: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "query": query,
            "status": status,
            "results": results,
            "audit": {
                "result_count": len(results),
                "db_path": str(self.db_path),
            },
        }

    def _normalize_query(self, query: str) -> str:
        tokens = TOKEN_RE.findall(query)
        return " ".join(tokens)


