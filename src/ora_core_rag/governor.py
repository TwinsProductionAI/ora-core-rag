"""Local RAG Governor configuration and runtime checks."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .index import ORACoreIndex
from .orchestrator import ORAOrchestratorConnector
from .registry import RAGRegistry
from .route_gate import ClientRouteGate


class GovernorError(ValueError):
    """Raised when the local RAG Governor configuration is invalid."""


@dataclass(frozen=True)
class GovernorConfig:
    """Resolved RAG Governor configuration."""

    path: Path
    data: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "GovernorConfig":
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise GovernorError("Governor config must be a JSON object.")
        return cls(path=config_path, data=data)

    @property
    def root(self) -> Path:
        return self.path.parent.parent if self.path.parent.name == "examples" else self.path.parent

    @property
    def profile(self) -> str:
        return str(self.data.get("profile", "local-governor"))

    def resolve_path(self, key: str) -> Path:
        value = self.data.get(key)
        if value is None:
            raise GovernorError(f"Governor config is missing {key!r}.")
        return self._resolve(value)

    def resolve_nested_path(self, section: str, key: str) -> Path:
        container = self.data.get(section)
        if not isinstance(container, dict) or key not in container:
            raise GovernorError(f"Governor config is missing {section}.{key}.")
        return self._resolve(container[key])

    def _resolve(self, value: Any) -> Path:
        path = Path(str(value))
        if path.is_absolute():
            return path
        return self.root / path

    @property
    def defaults(self) -> dict[str, Any]:
        defaults = self.data.get("defaults", {})
        if not isinstance(defaults, dict):
            raise GovernorError("Governor defaults must be a JSON object.")
        return defaults


class RAGGovernor:
    """Local RAG Governor runtime.

    The governor wires together ORA_CORE_RAG, the GLK route gate, the multi-RAG
    registry and Neroflux fanout policy. It does not store client payloads in the
    ORA core index.
    """

    def __init__(self, config: GovernorConfig):
        self.config = config

    @classmethod
    def from_path(cls, path: str | Path) -> "RAGGovernor":
        return cls(GovernorConfig.load(path))

    def status(self) -> dict[str, Any]:
        db_path = self.config.resolve_nested_path("paths", "db")
        audit_path = self.config.resolve_nested_path("paths", "audit_log")
        route_manifest = self.config.resolve_path("route_manifest")
        registry_path = self.config.resolve_path("rag_registry")
        sources_manifest = self.config.resolve_path("sources_manifest")

        route_status = self._route_status(route_manifest)
        registry_status = self._registry_status(registry_path)
        sqlite_status = self._sqlite_status()

        return {
            "module": "RAG_GOVERNOR",
            "version": "0.4.0",
            "profile": self.config.profile,
            "ready": bool(route_status["valid"] and registry_status["valid"] and sqlite_status["fts5_available"]),
            "environment": {
                "python": sys.version.split()[0],
                "sqlite": sqlite3.sqlite_version,
                "sqlite_fts5": sqlite_status["fts5_available"],
            },
            "paths": {
                "db": str(db_path),
                "audit_log": str(audit_path),
                "sources_manifest": str(sources_manifest),
                "route_manifest": str(route_manifest),
                "rag_registry": str(registry_path),
            },
            "state": {
                "db_exists": db_path.exists(),
                "audit_log_exists": audit_path.exists(),
                "sources_manifest_exists": sources_manifest.exists(),
            },
            "route": route_status,
            "registry": registry_status,
        }

    def bootstrap(self, *, ingest: bool = True) -> dict[str, Any]:
        db_path = self.config.resolve_nested_path("paths", "db")
        audit_path = self.config.resolve_nested_path("paths", "audit_log")
        index = ORACoreIndex(db_path, audit_log=audit_path)
        index.initialize()

        ingested: list[dict[str, Any]] = []
        if ingest:
            ingested = index.ingest_manifest(self.config.resolve_path("sources_manifest"))

        route = ClientRouteGate().load_manifest(self.config.resolve_path("route_manifest"))
        registry = RAGRegistry.from_path(self.config.resolve_path("rag_registry"))
        plan = registry.plan(
            route_manifest=route,
            neroflux_signal=self.config.defaults.get("neroflux_signal", {}),
        )

        index.audit.emit(
            "governor_bootstrap",
            {
                "profile": self.config.profile,
                "ingest": ingest,
                "source_count": len(ingested),
                "selected_count": len(plan["selected"]),
                "denied_count": len(plan["denied"]),
            },
        )

        return {
            "module": "RAG_GOVERNOR",
            "version": "0.4.0",
            "status": "BOOTSTRAPPED",
            "db": str(db_path),
            "audit_log": str(audit_path),
            "ingested": ingested,
            "plan": plan,
        }

    def run(self, *, query: str | None = None) -> dict[str, Any]:
        defaults = self.config.defaults
        db_path = self.config.resolve_nested_path("paths", "db")
        audit_path = self.config.resolve_nested_path("paths", "audit_log")
        index = ORACoreIndex(db_path, audit_log=audit_path)
        route = ClientRouteGate().load_manifest(self.config.resolve_path("route_manifest"))
        registry = RAGRegistry.from_path(self.config.resolve_path("rag_registry"))
        query_text = query or str(defaults.get("query", "")).strip()
        if not query_text:
            raise GovernorError("Governor run requires a query.")

        connector = ORAOrchestratorConnector(index)
        retrieval_packet = connector.route({
            "request_id": defaults.get("request_id"),
            "query": query_text,
            "intent": defaults.get("intent", "governed_retrieval"),
            "risk_level": defaults.get("risk_level", "MID"),
            "freshness_need": defaults.get("freshness_need", "LOW"),
            "source_required": defaults.get("source_required", True),
            "top_k": defaults.get("top_k", 5),
        })
        plan = registry.plan(
            route_manifest=route,
            neroflux_signal=defaults.get("neroflux_signal", {}),
        )
        index.audit.emit(
            "governor_run",
            {
                "query": query_text,
                "retrieval_status": retrieval_packet["retrieval"]["status"],
                "verify_status": retrieval_packet["verify_status"],
                "selected_count": len(plan["selected"]),
                "denied_count": len(plan["denied"]),
            },
        )
        return {
            "module": "RAG_GOVERNOR",
            "version": "0.4.0",
            "profile": self.config.profile,
            "retrieval_packet": retrieval_packet,
            "client_plan": plan,
        }

    def _route_status(self, path: Path) -> dict[str, Any]:
        try:
            route = ClientRouteGate().load_manifest(path)
            return {"valid": True, "route_id": route["route_id"], "tenant_id": route["tenant_id"]}
        except Exception as exc:  # noqa: BLE001 - status command should report all config failures.
            return {"valid": False, "error": str(exc)}

    def _registry_status(self, path: Path) -> dict[str, Any]:
        try:
            registry = RAGRegistry.from_path(path)
            return {"valid": True, "entry_count": len(registry.entries)}
        except Exception as exc:  # noqa: BLE001 - status command should report all config failures.
            return {"valid": False, "error": str(exc)}

    def _sqlite_status(self) -> dict[str, Any]:
        try:
            with sqlite3.connect(":memory:") as db:
                db.execute("CREATE VIRTUAL TABLE test_fts USING fts5(text)")
            return {"fts5_available": True}
        except sqlite3.Error as exc:
            return {"fts5_available": False, "error": str(exc)}
