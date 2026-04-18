"""Client route isolation gate for future tenant RAGs and agents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .hashing import sha256_json

ROUTE_RE = re.compile(r"^GLK\[TENANT:([A-Z0-9_-]+):(DEV|STAGE|PROD):v([0-9]+)\]$")


class RouteGateError(ValueError):
    """Raised when a route manifest or authorization request is invalid."""


class ClientRouteGate:
    """Validate GLK tenant routes and authorize scoped resources."""

    def load_manifest(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8-sig") as handle:
            manifest = json.load(handle)
        if not isinstance(manifest, dict):
            raise RouteGateError("Route manifest must be a JSON object.")
        return self.validate_manifest(manifest)

    def validate_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        route_id = str(manifest.get("route_id", "")).strip()
        match = ROUTE_RE.match(route_id)
        if not match:
            raise RouteGateError("Invalid route_id. Expected GLK[TENANT:<TENANT_ID>:<ENV>:v<N>].")

        tenant_from_route, env_from_route, _version = match.groups()
        tenant_id = str(manifest.get("tenant_id", "")).strip()
        environment = str(manifest.get("environment", "")).strip().lower()
        isolation = str(manifest.get("isolation", "")).strip().lower()

        if tenant_id != tenant_from_route:
            raise RouteGateError("Route tenant does not match manifest tenant_id.")
        if environment != env_from_route.lower():
            raise RouteGateError("Route environment does not match manifest environment.")
        if isolation != "strict":
            raise RouteGateError("Client route isolation must be strict.")

        normalized = dict(manifest)
        normalized.setdefault("allowed_rags", [])
        normalized.setdefault("allowed_agents", [])
        normalized.setdefault("forbidden_scopes", ["OTHER_TENANTS", "UNSCOPED_MEMORY"])
        normalized["manifest_hash"] = sha256_json({k: v for k, v in normalized.items() if k != "manifest_hash"})
        return normalized

    def require_route(self, manifest: dict[str, Any] | None) -> dict[str, Any]:
        if manifest is None:
            raise RouteGateError("Client RAG access requires a valid GLK route manifest.")
        return self.validate_manifest(manifest)

    def authorize(self, manifest: dict[str, Any] | None, *, resource_type: str, resource_id: str) -> dict[str, Any]:
        route = self.require_route(manifest)
        resource_id = str(resource_id).strip()
        resource_type = str(resource_type).strip().lower()
        tenant_id = str(route["tenant_id"])

        if resource_id.startswith("ORA_CORE_PRIVATE"):
            return self._decision(False, "blocked_private_core_scope", route, resource_type, resource_id)

        if "_" in resource_id:
            resource_tenant = resource_id.split("_", 1)[0]
            if resource_tenant and resource_tenant != tenant_id and resource_tenant != "ORA":
                return self._decision(False, "blocked_cross_tenant_access", route, resource_type, resource_id)

        allowed_key = "allowed_rags" if resource_type == "rag" else "allowed_agents" if resource_type == "agent" else ""
        if not allowed_key:
            return self._decision(False, "unsupported_resource_type", route, resource_type, resource_id)

        if resource_id not in set(route.get(allowed_key, [])):
            return self._decision(False, "resource_not_allowed_for_route", route, resource_type, resource_id)

        return self._decision(True, "allowed", route, resource_type, resource_id)

    def _decision(self, allowed: bool, reason: str, route: dict[str, Any], resource_type: str, resource_id: str) -> dict[str, Any]:
        return {
            "allowed": allowed,
            "reason": reason,
            "route_id": route.get("route_id"),
            "tenant_id": route.get("tenant_id"),
            "resource_type": resource_type,
            "resource_id": resource_id,
        }
