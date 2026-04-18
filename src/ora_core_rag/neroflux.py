"""Deterministic Neroflux fanout regulation for multi-RAG routing."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

NUMERIC_FIELDS = (
    "retrieval_pressure",
    "source_conflict",
    "permission_risk",
    "injection_risk",
    "latency_pressure",
    "cost_pressure",
    "client_sensitivity",
    "urgency",
)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def normalize_signal(signal: dict[str, Any] | None) -> dict[str, Any]:
    normalized = deepcopy(signal or {})
    for field in NUMERIC_FIELDS:
        try:
            normalized[field] = clamp(float(normalized.get(field, 0.0)))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Neroflux field {field!r} must be numeric.") from exc

    try:
        normalized["agent_count"] = max(0, int(normalized.get("agent_count", 0)))
    except (TypeError, ValueError) as exc:
        raise ValueError("Neroflux field 'agent_count' must be an integer.") from exc

    normalized["contradiction"] = bool(normalized.get("contradiction", False))
    return normalized


class NerofluxFanoutRegulator:
    """Regulate multi-RAG fanout before client resources are activated."""

    def regulate(self, signal: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized = normalize_signal(signal)
        load = self._build_load(normalized)
        pace = self._select_pace(normalized, load)
        actions = self._select_actions(normalized, load, pace)
        max_rag_fanout = self._select_max_fanout(normalized, load)
        top_k_per_rag = self._select_top_k(normalized, load)
        require_hnerons = self._require_hnerons(normalized, load)
        require_human_review = self._require_human_review(normalized, load)

        return {
            "module": "NEROFLUX_FANOUT_REGULATOR",
            "version": "0.3.0",
            "pace": pace,
            "max_rag_fanout": max_rag_fanout,
            "top_k_per_rag": top_k_per_rag,
            "require_hnerons": require_hnerons,
            "require_human_review": require_human_review,
            "load": load,
            "actions": actions,
            "trace": [
                f"pressure evaluated at {load['total_pressure']}",
                f"pace selected: {pace}",
                f"max rag fanout: {max_rag_fanout}",
                f"top_k per rag: {top_k_per_rag}",
                f"actions selected: {', '.join(actions)}",
            ],
        }

    def _build_load(self, signal: dict[str, Any]) -> dict[str, float]:
        agent_pressure = clamp(signal["agent_count"] / 5.0)
        security_pressure = max(signal["permission_risk"], signal["injection_risk"], signal["client_sensitivity"])
        operational_pressure = max(signal["latency_pressure"], signal["cost_pressure"], agent_pressure)
        evidence_pressure = max(signal["retrieval_pressure"], signal["source_conflict"])
        total = round((security_pressure + operational_pressure + evidence_pressure + signal["urgency"]) / 4, 3)
        return {
            "agent_pressure": round(agent_pressure, 3),
            "security_pressure": round(security_pressure, 3),
            "operational_pressure": round(operational_pressure, 3),
            "evidence_pressure": round(evidence_pressure, 3),
            "total_pressure": total,
        }

    def _select_pace(self, signal: dict[str, Any], load: dict[str, float]) -> str:
        if signal["contradiction"] or signal["urgency"] >= 0.75:
            return "fast"
        if load["security_pressure"] >= 0.70 or load["total_pressure"] >= 0.68:
            return "slow"
        return "balanced"

    def _select_max_fanout(self, signal: dict[str, Any], load: dict[str, float]) -> int:
        if load["security_pressure"] >= 0.70 or signal["contradiction"]:
            return 1
        if load["total_pressure"] >= 0.68 or load["operational_pressure"] >= 0.70:
            return 1
        if load["evidence_pressure"] >= 0.55:
            return 2
        return 3

    def _select_top_k(self, signal: dict[str, Any], load: dict[str, float]) -> int:
        if load["security_pressure"] >= 0.70:
            return 3
        if load["operational_pressure"] >= 0.70 or load["total_pressure"] >= 0.68:
            return 4
        if signal["retrieval_pressure"] >= 0.70:
            return 6
        return 5

    def _require_hnerons(self, signal: dict[str, Any], load: dict[str, float]) -> bool:
        return bool(signal["contradiction"] or signal["source_conflict"] >= 0.35 or load["security_pressure"] >= 0.55)

    def _require_human_review(self, signal: dict[str, Any], load: dict[str, float]) -> bool:
        return bool(signal["source_conflict"] >= 0.80 or signal["permission_risk"] >= 0.85 or signal["injection_risk"] >= 0.85)

    def _select_actions(self, signal: dict[str, Any], load: dict[str, float], pace: str) -> list[str]:
        actions: list[str] = []

        if load["security_pressure"] >= 0.55:
            actions.append("require_access_check")
            actions.append("isolate_client_context")

        if signal["injection_risk"] >= 0.55:
            actions.append("require_prompt_injection_scan")

        if load["operational_pressure"] >= 0.60:
            actions.append("cap_rag_fanout")

        if load["operational_pressure"] >= 0.70:
            actions.append("prefer_cached_context")
            actions.append("reduce_top_k")

        if signal["source_conflict"] >= 0.35 or signal["contradiction"]:
            actions.append("require_hnerons_pre_emit")

        if signal["source_conflict"] >= 0.80:
            actions.append("route_to_human_review")

        if pace == "slow":
            actions.append("reduce_exchange_velocity")

        if not actions:
            actions.append("maintain_balanced_circulation")

        return actions
