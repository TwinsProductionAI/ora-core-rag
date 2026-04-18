# ORA_CORE_RAG

Canonical retrieval layer for ORA_CORE_OS.

Status: `0.2.0`

`ORA_CORE_RAG` is a local-first, deterministic retrieval engine for the public ORA canon. It indexes ORA technical files, retrieves source-backed context, emits audit traces, and keeps client data outside the core memory boundary.

## V0.2 Capabilities

- automatic discovery and ingestion from public GitHub repositories
- optional JSONL audit log for indexing, queries and orchestrator packets
- minimal `ORCHESTRATEUR_LLM` connector returning a routed retrieval packet
- SQLite FTS5 exact text retrieval
- deterministic source and chunk hashes
- GLK client route gate for future tenant RAG isolation

## Quick Start

```powershell
cd C:\ora-core-rag
python -m unittest discover -s tests
python -m pip install -e .
```

Create a local index:

```powershell
python -m ora_core_rag init --db data/index/ora_core_rag.sqlite
python -m ora_core_rag ingest --manifest examples/ora_sources.json --db data/index/ora_core_rag.sqlite --audit-log data/audit/local.jsonl
python -m ora_core_rag query "PRIMORDIA truth layer" --db data/index/ora_core_rag.sqlite --audit-log data/audit/local.jsonl
```

Discover public GitHub sources without ingesting:

```powershell
python -m ora_core_rag discover-github TwinsProductionAI/ora-core-specs --ref main --limit 10
```

Ingest a public GitHub repository directly:

```powershell
python -m ora_core_rag ingest-github TwinsProductionAI/ora-core-specs --ref main --limit 20 --db data/index/ora_core_rag.sqlite --audit-log data/audit/local.jsonl
```

Return an orchestrator-shaped retrieval packet:

```powershell
python -m ora_core_rag orchestrate-query "ORCHESTRATEUR_LLM verification" --risk-level MID --db data/index/ora_core_rag.sqlite
```

## Architecture

```text
User request
  |
  v
ORCHESTRATEUR_LLM
  |
  v
Neroflux
  |
  v
ORA_CORE_RAG
  |-- canonical ORA retrieval only
  |-- source hashes
  |-- FTS5 text index
  |-- JSONL audit trace
  |-- GitHub public source discovery
  |
  v
Client Route Gate
  |-- GLK tenant route required for future client RAGs
  |-- no cross-tenant access
  |-- no client writes to ORA core
```

## Core Rule

```text
ORA_CORE_RAG indexes ORA canon only.
Client RAGs require a GLK tenant route and stay outside the core index.
```

## Non-Goals

- it is not a vector database
- it is not a client document store
- it is not a final answer generator
- it is not a truth engine by itself
- it does not write client data into ORA core memory
