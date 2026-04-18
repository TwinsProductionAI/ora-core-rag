# MODULE_ORA_CORE_RAG

Version: `0.1.0`

## Definition

`ORA_CORE_RAG` is the canonical retrieval layer for `ORA_CORE_OS`. It indexes public ORA sources, retrieves source-backed context, and produces audit-friendly retrieval packets for the larger ORA pipeline.

It is intentionally small in v0.1:

- Python standard library runtime
- SQLite FTS5 text retrieval
- deterministic chunk hashes
- JSON manifests
- route gate for future client RAG isolation

## Authority Position

`ORA_CORE_RAG` does not override:

1. system or project instructions
2. `ORCHESTRATEUR_LLM`
3. `HGOV` / `Primordia`
4. `GPV2`
5. `H-NERONS`

It supplies canon evidence. It does not decide final truth.

## Security Rules

- deny non-`ORA_CORE` document ingestion
- deny client retrieval without a valid route manifest
- deny cross-tenant RAG or agent access
- route IDs must be opaque and non-sensitive
- route manifests can be stored, but client content cannot

## Future Modules

Later versions can add embeddings, graph retrieval, FastAPI, n8n hooks, live GitHub reindexing and client RAG connectors.
