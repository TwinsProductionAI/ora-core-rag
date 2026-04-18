"""Minimal ORCHESTRATEUR_LLM connector for ORA_CORE_RAG."""

from __future__ import annotations

from typing import Any

from .index import ORACoreIndex

RISK_LEVELS_REQUIRING_VERIFICATION = {"MID", "HIGH", "CRITICAL"}
FRESHNESS_REQUIRING_VERIFICATION = {"RECENT", "UNSTABLE", "HIGH"}


class ORAOrchestratorConnector:
    """Build retrieval packets shaped for ORCHESTRATEUR_LLM.

    The connector does not generate final answers. It returns source-backed ORA
    context plus verification status for upstream synthesis.
    """

    def __init__(self, index: ORACoreIndex):
        self.index = index

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        query = str(request.get("query", "")).strip()
        top_k = int(request.get("top_k", 5))
        risk_level = str(request.get("risk_level", "LOW")).upper()
        freshness_need = str(request.get("freshness_need", "LOW")).upper()
        source_required = bool(request.get("source_required", True))

        retrieval = self.index.query(query, top_k=top_k)
        verify_status = self._verify_status(
            retrieval_status=retrieval["status"],
            risk_level=risk_level,
            freshness_need=freshness_need,
            source_required=source_required,
        )

        return {
            "module": "ORA_CORE_RAG_ORCHESTRATOR_CONNECTOR",
            "version": "0.2.0",
            "request_id": request.get("request_id"),
            "intent": request.get("intent", "canonical_retrieval"),
            "risk_level": risk_level,
            "freshness_need": freshness_need,
            "primary_module": "ORA_CORE_RAG",
            "secondary_modules": request.get("secondary_modules", []),
            "verify_status": verify_status,
            "authority_path": [
                "SYSTEM_OR_PROJECT_INSTRUCTIONS",
                "ORCHESTRATEUR_LLM",
                "HGOV_OR_PRIMORDIA",
                "GPV2",
                "ORA_CORE_RAG",
            ],
            "retrieval": retrieval,
        }

    def _verify_status(self, *, retrieval_status: str, risk_level: str, freshness_need: str, source_required: bool) -> str:
        if retrieval_status == "UNSURE" and source_required:
            return "UNAVAILABLE"
        if risk_level in RISK_LEVELS_REQUIRING_VERIFICATION or freshness_need in FRESHNESS_REQUIRING_VERIFICATION:
            return "RECOMMENDED"
        return "NOT_NEEDED"
