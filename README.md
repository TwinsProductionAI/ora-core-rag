# ORA_CORE_RAG

Canonical retrieval and multi-RAG control layer for ORA_CORE_OS.

Status: `0.3.0`

`ORA_CORE_RAG` is a local-first, deterministic retrieval engine for the public ORA canon. It indexes ORA technical files, retrieves source-backed context, emits audit traces, and keeps client data outside the core memory boundary.

## V0.3 Capabilities

- automatic discovery and ingestion from public GitHub repositories
- optional JSONL audit log for indexing, queries and orchestrator packets
- minimal `ORCHESTRATEUR_LLM` connector returning a routed retrieval packet
- GLK client route gate for tenant isolation
- multi-RAG / agent registry planning
- deterministic Neroflux fanout regulation
- anti-contamination checks for cross-tenant resources

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

Regulate fanout with Neroflux:

```powershell
python -m ora_core_rag neroflux-regulate --client-sensitivity 0.9 --permission-risk 0.7 --agent-count 4
```

Build a route-gated client activation plan:

```powershell
python -m ora_core_rag plan-client --route-manifest examples/client_route_manifest.json --registry examples/rag_registry.json --client-sensitivity 0.4
```

## Architecture

```text
User request
  |
  v
ORCHESTRATEUR_LLM
  |
  v
Neroflux fanout regulator
  |-- caps RAG fanout
  |-- reduces top_k under pressure
  |-- requires H-NERONS when conflict or sensitivity rises
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
Client Route Gate + RAG Registry
  |-- GLK tenant route required for client RAGs
  |-- registry entries cannot answer final directly
  |-- cross-tenant access denied
  |-- no client writes to ORA core
```

## Core Rule

```text
ORA_CORE_RAG indexes ORA canon only.
Client RAGs require a GLK tenant route and stay outside the core index.
Neroflux can reduce fanout, but truth still goes through HGOV/H-NERONS/Primordia.
```

## Non-Goals

- it is not a vector database
- it is not a client document store
- it is not a final answer generator
- it is not a truth engine by itself
- it does not write client data into ORA core memory
