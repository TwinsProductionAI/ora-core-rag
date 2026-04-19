# MODULE_ORA_CORE_RAG

Version: `0.4.0`

## Definition

`ORA_CORE_RAG` is the canonical retrieval, multi-RAG control and local RAG Governor layer for `ORA_CORE_OS`. It indexes public ORA sources, retrieves source-backed context, produces audit-friendly retrieval packets, plans isolated client RAG/agent activation, and can bootstrap a local governed runtime profile.

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
- local RAG Governor runtime and configuration

## Authority Position

`ORA_CORE_RAG` does not override:

1. system or project instructions
2. `ORCHESTRATEUR_LLM`
3. `HGOV` / `Primordia`
4. `GPV2`
5. `H-NERONS`

It supplies canon evidence and activation plans. It does not decide final truth.

## V0.4 Runtime Flow

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

GOVERNOR_FLOW
  -> LOAD_LOCAL_GOVERNOR_CONFIG
  -> CHECK_PYTHON_SQLITE_FTS5
  -> INIT_INDEX_AND_AUDIT
  -> INGEST_ORA_CANON
  -> VALIDATE_GLK_ROUTE_AND_REGISTRY
  -> RUN_ORCHESTRATED_RETRIEVAL_AND_CLIENT_PLAN
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
- RAG Governor config wires local runtime only; it does not bypass HGOV/H-NERONS/Primordia

## Future Modules

Later versions can add embeddings, graph retrieval, FastAPI, n8n hooks, Podman service profiles, live GitHub webhooks and real client RAG connectors.

## ARCH+ M10 Implant

`ORA_CORE_RAG` now includes a small ARCH+ v3 implant for `MODULE_ARCH_PLUS` at code position `M10`.

It builds route-gated ArchiPersona activation packets and keeps private client profile payloads outside the ORA core index.

Files:

- `src/ora_core_rag/arch_persona.py`
- `schemas/arch_persona_activation.schema.json`
- `examples/arch_persona_activation.json`
- `specs/ORA_CORE_RAG_ARCH_PLUS_IMPLANT_V1_0.json`
- `docs/ARCH_PLUS_IMPLANT.md`
- `tests/test_arch_persona.py`
