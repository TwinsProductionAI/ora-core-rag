# MODULE_ORA_CORE_RAG

Version: `0.3.0`

## Definition

`ORA_CORE_RAG` is the canonical retrieval and multi-RAG control layer for `ORA_CORE_OS`. It indexes public ORA sources, retrieves source-backed context, produces audit-friendly retrieval packets, and plans isolated client RAG/agent activation.

It remains intentionally small:

- Python standard library runtime
- SQLite FTS5 text retrieval
- deterministic chunk hashes
- JSON manifests
- public GitHub source discovery
- JSONL audit logging
- GLK route gate for client RAG isolation
- multi-RAG / agent registry
- deterministic Neroflux fanout regulation
- minimal `ORCHESTRATEUR_LLM` connector

## Authority Position

`ORA_CORE_RAG` does not override:

1. system or project instructions
2. `ORCHESTRATEUR_LLM`
3. `HGOV` / `Primordia`
4. `GPV2`
5. `H-NERONS`

It supplies canon evidence and activation plans. It does not decide final truth.

## V0.3 Runtime Flow

```text
LOAD_OR_DISCOVER_SOURCES
  -> FETCH_OR_READ_SOURCE
  -> HASH_SOURCE
  -> CHUNK_SOURCE
  -> INDEX_CHUNKS_FTS5
  -> RETRIEVE_SOURCE_BACKED_CONTEXT
  -> OPTIONAL_ORCHESTRATEUR_LLM_PACKET
  -> OPTIONAL_JSONL_AUDIT

CLIENT_ACTIVATION_FLOW
  -> VALIDATE_GLK_ROUTE
  -> LOAD_RAG_REGISTRY
  -> AUTHORIZE_RESOURCE_IDS
  -> NEROFLUX_FANOUT_REGULATION
  -> SELECT_ALLOWED_RAGS_AND_AGENTS
  -> DENY_CROSS_TENANT_OR_OVERFLOW
```

## Security Rules

- deny non-`ORA_CORE` document ingestion
- deny client retrieval without a valid route manifest
- deny cross-tenant RAG or agent access
- route IDs must be opaque and non-sensitive
- registry entries cannot set `can_answer_final=true`
- route manifests can be stored, but client content cannot
- audit logs should store retrieval metadata, not private client payloads
- Neroflux regulates circulation only; it does not govern truth

## Future Modules

Later versions can add embeddings, graph retrieval, FastAPI, n8n hooks, live GitHub webhooks and real client RAG connectors.
