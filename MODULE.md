# MODULE_ORA_CORE_RAG

Version: `0.2.0`

## Definition

`ORA_CORE_RAG` is the canonical retrieval layer for `ORA_CORE_OS`. It indexes public ORA sources, retrieves source-backed context, and produces audit-friendly retrieval packets for the larger ORA pipeline.

It remains intentionally small:

- Python standard library runtime
- SQLite FTS5 text retrieval
- deterministic chunk hashes
- JSON manifests
- public GitHub source discovery
- JSONL audit logging
- route gate for future client RAG isolation
- minimal `ORCHESTRATEUR_LLM` connector

## Authority Position

`ORA_CORE_RAG` does not override:

1. system or project instructions
2. `ORCHESTRATEUR_LLM`
3. `HGOV` / `Primordia`
4. `GPV2`
5. `H-NERONS`

It supplies canon evidence. It does not decide final truth.

## V0.2 Runtime Flow

```text
LOAD_OR_DISCOVER_SOURCES
  -> FETCH_OR_READ_SOURCE
  -> HASH_SOURCE
  -> CHUNK_SOURCE
  -> INDEX_CHUNKS_FTS5
  -> RETRIEVE_SOURCE_BACKED_CONTEXT
  -> EMIT_JSONL_AUDIT_OPTIONAL
  -> RETURN_ORCHESTRATOR_PACKET_OPTIONAL
```

## Security Rules

- deny non-`ORA_CORE` document ingestion
- deny client retrieval without a valid route manifest
- deny cross-tenant RAG or agent access
- route IDs must be opaque and non-sensitive
- route manifests can be stored, but client content cannot
- audit logs should store retrieval metadata, not private client payloads

## Future Modules

Later versions can add embeddings, graph retrieval, FastAPI, n8n hooks, live GitHub webhooks and client RAG connectors.
