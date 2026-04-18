"""Multi-RAG registry and activation planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .neroflux import NerofluxFanoutRegulator
from .route_gate import ClientRouteGate

ALLOWED_RESOURCE_TYPES = {"rag", "agent", "llm"}
CLIENT_SCOPES = {"TENANT", "DEPARTMENT", "PRIVATE_CASE"}


class RegistryError(ValueError):
    """Raised when a RAG registry is invalid."""


def load_registry(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        registry = json.load(handle)
    if not isinstance(registry, dict):
        raise RegistryError("Registry root must be a JSON object.")
    return registry


class RAGRegistry:
    """Validate and query a registry of RAGs, agents and LLM adapters."""

    def __init__(self, registry: dict[str, Any]):
        self.registry = registry
        self.entries = self._validate_entries(registry)
        self.by_id = {entry["id"]: entry for entry in self.entries}

    @classmethod
    def from_path(cls, path: str | Path) -> "RAGRegistry":
        return cls(load_registry(path))

    def get(self, resource_id: str) -> dict[str, Any] | None:
        return self.by_id.get(resource_id)

    def plan(
        self,
        *,
        route_manifest: dict[str, Any],
        requested_ids: list[str] | None = None,
        neroflux_signal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        gate = ClientRouteGate()
        route = gate.validate_manifest(route_manifest)
        requested = requested_ids or self._default_requested_ids(route)
        regulator = NerofluxFanoutRegulator()
        fanout = regulator.regulate(self._augment_signal(neroflux_signal, requested))

        authorized: list[dict[str, Any]] = []
        denied: list[dict[str, Any]] = []

        for resource_id in requested:
            entry = self.get(resource_id)
            if not entry:
                denied.append(self._denial(resource_id, "unknown", "resource_not_in_registry"))
                continue

            decision = self._authorize_entry(gate, route, entry)
            if decision["allowed"]:
                authorized.append({"entry": entry, "decision": decision})
            else:
                denied.append({"entry": entry, "decision": decision})

        selected, overflow = self._apply_fanout_cap(authorized, fanout["max_rag_fanout"])
        denied.extend(overflow)

        return {
            "module": "ORA_MULTI_RAG_REGISTRY",
            "version": "0.3.0",
            "route_id": route["route_id"],
            "tenant_id": route["tenant_id"],
            "requested": requested,
            "selected": [item["entry"] for item in selected],
            "denied": denied,
            "fanout": fanout,
            "policy": {
                "client_payload_to_core": "DENY",
                "cross_tenant_access": "DENY",
                "can_answer_final": False,
            },
        }

    def _validate_entries(self, registry: dict[str, Any]) -> list[dict[str, Any]]:
        entries = registry.get("entries")
        if not isinstance(entries, list):
            raise RegistryError("Registry requires an entries array.")

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise RegistryError("Registry entries must be JSON objects.")
            resource_id = str(entry.get("id", "")).strip()
            resource_type = str(entry.get("type", "")).strip().lower()
            scope = str(entry.get("scope", "")).strip().upper()
            can_answer_final = bool(entry.get("can_answer_final", False))

            if not resource_id:
                raise RegistryError("Registry entry is missing id.")
            if resource_id in seen:
                raise RegistryError(f"Duplicate registry id: {resource_id}")
            if resource_type not in ALLOWED_RESOURCE_TYPES:
                raise RegistryError(f"Unsupported resource type for {resource_id}: {resource_type}")
            if can_answer_final:
                raise RegistryError(f"Registry entry {resource_id} cannot answer final directly.")
            if scope in CLIENT_SCOPES and not entry.get("tenant_id"):
                raise RegistryError(f"Client-scoped entry {resource_id} requires tenant_id.")

            normalized_entry = dict(entry)
            normalized_entry["id"] = resource_id
            normalized_entry["type"] = resource_type
            normalized_entry["scope"] = scope
            normalized_entry.setdefault("source_required", True)
            normalized_entry["can_answer_final"] = False
            normalized.append(normalized_entry)
            seen.add(resource_id)

        return normalized

    def _default_requested_ids(self, route: dict[str, Any]) -> list[str]:
        return list(route.get("allowed_rags", [])) + list(route.get("allowed_agents", []))

    def _augment_signal(self, signal: dict[str, Any] | None, requested_ids: list[str]) -> dict[str, Any]:
        normalized = dict(signal or {})
        if not normalized.get("agent_count"):
            normalized["agent_count"] = len(requested_ids)
        normalized.setdefault("retrieval_pressure", min(1.0, len(requested_ids) / 4.0))
        return normalized

    def _authorize_entry(self, gate: ClientRouteGate, route: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
        scope = entry["scope"]
        resource_id = entry["id"]
        resource_type = entry["type"]
        tenant_id = str(route["tenant_id"])

        if scope == "ORA_CORE":
            return {
                "allowed": resource_id == "ORA_CORE_RAG",
                "reason": "allowed_core_resource" if resource_id == "ORA_CORE_RAG" else "blocked_private_core_scope",
                "route_id": route["route_id"],
                "tenant_id": tenant_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }

        if str(entry.get("tenant_id", "")) != tenant_id:
            return {
                "allowed": False,
                "reason": "blocked_cross_tenant_access",
                "route_id": route["route_id"],
                "tenant_id": tenant_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }

        if resource_type not in {"rag", "agent"}:
            return {
                "allowed": False,
                "reason": "resource_type_requires_adapter_policy",
                "route_id": route["route_id"],
                "tenant_id": tenant_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }

        return gate.authorize(route, resource_type=resource_type, resource_id=resource_id)

    def _apply_fanout_cap(self, authorized: list[dict[str, Any]], max_rag_fanout: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        selected: list[dict[str, Any]] = []
        overflow: list[dict[str, Any]] = []
        rag_count = 0

        for item in authorized:
            entry = item["entry"]
            if entry["type"] == "rag":
                if rag_count >= max_rag_fanout:
                    overflow.append({"entry": entry, "decision": {"allowed": False, "reason": "blocked_by_neroflux_fanout_cap"}})
                    continue
                rag_count += 1
            selected.append(item)

        return selected, overflow

    def _denial(self, resource_id: str, resource_type: str, reason: str) -> dict[str, Any]:
        return {
            "entry": {"id": resource_id, "type": resource_type},
            "decision": {"allowed": False, "reason": reason, "resource_id": resource_id, "resource_type": resource_type},
        }


