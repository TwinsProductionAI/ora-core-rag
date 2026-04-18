# ORA_CORE_RAG

Canonical retrieval layer for ORA_CORE_OS.

Status: `0.1.0`

`ORA_CORE_RAG` is a local-first, deterministic retrieval engine for the public ORA canon. It is designed to index ORA technical files, retrieve source-backed context, and keep client data outside the core memory boundary.

## Goals

- index ORA public canon files with stable source hashes
- preserve source path, URI, scope, tags and chunk hashes
- retrieve exact module names such as `PRIMORDIA`, `REM++`, `GL_G`, `CODE_POS`
- expose uncertainty when no source supports a claim
- enforce a client route gate before any future tenant RAG access
- keep `ORA_CORE_RAG` read-only for client payloads

## Non-Goals

- it is not a vector database
- it is not a client document store
- it is not a final answer generator
- it is not a truth engine by itself
- it does not write client data into ORA core memory

## Quick Start

```powershell
cd C:\\ora-core-rag
python -m unittest discover -s tests
python -m pip install -e .
```

Create a local index:

```powershell
python -m ora_core_rag init --db data/index/ora_core_rag.sqlite
python -m ora_core_rag ingest --manifest examples/ora_sources.json --db data/index/ora_core_rag.sqlite
python -m ora_core_rag query "PRIMORDIA truth layer" --db data/index/ora_core_rag.sqlite
```

The example source manifest points to public GitHub raw files. Network access is only needed when ingesting those remote sources.

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
  |-- module graph-ready metadata
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

