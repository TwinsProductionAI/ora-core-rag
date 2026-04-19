# ARCH+ Implant for ORA_CORE_RAG

This document defines the ORA_CORE_RAG implant for ARCH+ v3, the advanced M10
Persona Genesis Engine.

## Scope

The implant builds an ArchiPersona activation packet from a JSON payload. It is
route-gated by `ClientRouteGate` and returns a structured profile with source
status per field.

It does not write client profile payloads into the ORA core index.

## Command

```powershell
python -m ora_core_rag arch-persona-activate --payload examples/arch_persona_activation.json
```

The command returns:

- `arch_plus.code_pos = M10`
- `arch_plus.variant_id = M10_ARCH_PLUS_V3`
- all six ArchiPersona foundation groups
- `source_summary` for `USER_PROVIDED`, `SUGGESTION`, `INCERTAIN`, `CANON`
- coherence test results
- policy fields denying core writes

## Field Source Policy

`USER_PROVIDED` means the user supplied the value.

`SUGGESTION` means ARCH+ proposed a safe default. It is not a fact.

`INCERTAIN` means no safe value exists yet.

`CANON` is reserved for values grounded in trusted ORA canon.

## RAG Boundary

ORA_CORE_RAG may index the public module spec, schema, tests and docs. Tenant
profile payloads must remain in tenant-scoped storage behind a valid GLK route.

## Files

- `src/ora_core_rag/arch_persona.py`
- `schemas/arch_persona_activation.schema.json`
- `examples/arch_persona_activation.json`
- `specs/ORA_CORE_RAG_ARCH_PLUS_IMPLANT_V1_0.json`
- `tests/test_arch_persona.py`