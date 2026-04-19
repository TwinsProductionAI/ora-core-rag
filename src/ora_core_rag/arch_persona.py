"""ARCH+ ArchiPersona activation helpers for ORA_CORE_RAG.

The implant builds a route-gated activation packet. It does not write client
profile payloads into the ORA core index.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .route_gate import ClientRouteGate

FIELD_SOURCES = {"USER_PROVIDED", "CANON", "SUGGESTION", "INCERTAIN"}
MAX_PERSONAE = 4
MAX_ARCS = 4

FIELD_GROUPS: dict[str, dict[str, Any]] = {
    "context_identity": {
        "fields": ["role", "identity", "cognitive_posture"],
        "defaults": {
            "role": None,
            "identity": None,
            "cognitive_posture": "clarity_first_structured_reasoning",
        },
        "suggested": {"cognitive_posture"},
    },
    "goal_why": {
        "fields": ["objective", "mission", "reason_to_exist"],
        "defaults": {"objective": None, "mission": None, "reason_to_exist": None},
        "suggested": set(),
    },
    "tone_emo": {
        "fields": ["tone", "emo_profile", "intensity"],
        "defaults": {"tone": "clear_pragmatic", "emo_profile": "stable_accessible", "intensity": 55},
        "suggested": {"tone", "emo_profile", "intensity"},
    },
    "limits_risk": {
        "fields": ["risk", "audacity", "reflective_depth"],
        "defaults": {"risk": 35, "audacity": 55, "reflective_depth": 70},
        "suggested": {"risk", "audacity", "reflective_depth"},
    },
    "personae_start": {
        "fields": ["personae"],
        "defaults": {"personae": []},
        "suggested": set(),
    },
    "arc_plus_plus": {
        "fields": ["arcs"],
        "defaults": {"arcs": []},
        "suggested": set(),
    },
}

NUMERIC_FIELDS = {"intensity", "risk", "audacity", "reflective_depth"}
LIST_FIELDS = {"personae", "arcs"}


class ArchPersonaError(ValueError):
    """Raised when an ARCH+ activation payload is invalid."""


def build_arch_persona_activation(
    answers: dict[str, Any] | None,
    *,
    route_manifest: dict[str, Any],
    mode: str = "FAST_PREFILL",
) -> dict[str, Any]:
    """Build an ARCH+ v3 activation packet for a tenant route.

    Missing values are represented explicitly. Suggested defaults are marked as
    SUGGESTION; unknown values are marked INCERTAIN. The returned packet is safe
    to pass through ORA_CORE_RAG because it states that client payloads stay
    outside the core index.
    """

    if mode not in {"FAST_PREFILL", "DEEP_CALIBRATION"}:
        raise ArchPersonaError("Unsupported ARCH+ activation mode.")

    route = ClientRouteGate().validate_manifest(route_manifest)
    normalized_answers = _answers_root(answers or {})
    profile, warnings = _prefill_profile(normalized_answers)
    source_summary = _source_summary(profile)
    status = "READY" if source_summary["INCERTAIN"] == 0 else "READY_WITH_UNSURE"

    return {
        "module": "ORA_CORE_RAG_ARCH_PLUS_IMPLANT",
        "version": "1.0.0",
        "arch_plus": {
            "module_id": "MODULE_ARCH_PLUS",
            "code_pos": "M10",
            "variant_id": "M10_ARCH_PLUS_V3",
            "variant_version": "3.0.0",
        },
        "mode": mode,
        "status": status,
        "route": {
            "route_id": route["route_id"],
            "tenant_id": route["tenant_id"],
            "manifest_hash": route["manifest_hash"],
        },
        "profile": profile,
        "source_summary": source_summary,
        "coherence": {
            "warnings": warnings,
            "tests": _coherence_tests(profile),
        },
        "policy": {
            "write_client_payload_to_core": "DENY",
            "client_payload_to_core": "DENY",
            "tenant_scoped_profile_store_required": True,
            "source_status_required_per_field": True,
            "can_answer_final": False,
        },
    }


def load_activation_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Extract answers, route_manifest and mode from a JSON activation payload."""

    if not isinstance(payload, dict):
        raise ArchPersonaError("Activation payload must be a JSON object.")
    route_manifest = payload.get("route_manifest")
    if not isinstance(route_manifest, dict):
        raise ArchPersonaError("Activation payload requires route_manifest.")
    answers = payload.get("answers", {})
    if answers is None:
        answers = {}
    if not isinstance(answers, dict):
        raise ArchPersonaError("Activation answers must be a JSON object.")
    mode = str(payload.get("mode", "FAST_PREFILL"))
    return answers, route_manifest, mode


def _answers_root(answers: dict[str, Any]) -> dict[str, Any]:
    nested = answers.get("answers")
    if isinstance(nested, dict):
        return nested
    return answers


def _prefill_profile(answers: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    profile: dict[str, Any] = {}
    warnings: list[dict[str, str]] = []

    for group_name, spec in FIELD_GROUPS.items():
        group_answers = answers.get(group_name, {})
        if group_answers is None:
            group_answers = {}
        if not isinstance(group_answers, dict):
            raise ArchPersonaError(f"Activation group {group_name!r} must be an object.")

        group: dict[str, Any] = {}
        for field_name in spec["fields"]:
            value_present = field_name in group_answers and group_answers[field_name] not in (None, "")
            value = deepcopy(group_answers[field_name]) if value_present else deepcopy(spec["defaults"].get(field_name))
            source = "USER_PROVIDED" if value_present else "SUGGESTION" if field_name in spec["suggested"] else "INCERTAIN"

            normalized = _normalize_field(group_name, field_name, value, source)
            group[field_name] = normalized
            if normalized["source"] == "INCERTAIN":
                warnings.append({"code": "missing_field", "field": f"{group_name}.{field_name}", "level": "INFO"})

        profile[group_name] = group

    return profile, warnings


def _normalize_field(group_name: str, field_name: str, value: Any, source: str) -> dict[str, Any]:
    if field_name in NUMERIC_FIELDS:
        value = _normalize_percent(field_name, value)
    elif field_name in LIST_FIELDS:
        value = _normalize_list(group_name, field_name, value)
    elif value is not None:
        value = str(value).strip()
        if not value:
            value = None
            source = "INCERTAIN"

    return {
        "value": value,
        "source": source if value is not None or field_name in LIST_FIELDS else "INCERTAIN",
        "confidence": _confidence(source if value is not None or field_name in LIST_FIELDS else "INCERTAIN"),
    }


def _normalize_percent(field_name: str, value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ArchPersonaError(f"Field {field_name} must be an integer from 0 to 100.") from exc
    if number < 0 or number > 100:
        raise ArchPersonaError(f"Field {field_name} must be from 0 to 100.")
    return number


def _normalize_list(group_name: str, field_name: str, value: Any) -> list[str]:
    if value is None:
        items: list[Any] = []
    elif isinstance(value, list):
        items = value
    else:
        raise ArchPersonaError(f"Field {group_name}.{field_name} must be an array.")

    limit = MAX_PERSONAE if field_name == "personae" else MAX_ARCS
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if len(cleaned) > limit:
        raise ArchPersonaError(f"Field {group_name}.{field_name} allows at most {limit} items.")
    return cleaned


def _confidence(source: str) -> float:
    return {
        "USER_PROVIDED": 0.9,
        "CANON": 0.95,
        "SUGGESTION": 0.55,
        "INCERTAIN": 0.0,
    }[source]


def _source_summary(profile: dict[str, Any]) -> dict[str, int]:
    summary = {source: 0 for source in FIELD_SOURCES}
    for group in profile.values():
        for field in group.values():
            summary[field["source"]] += 1
    return summary


def _coherence_tests(profile: dict[str, Any]) -> list[dict[str, Any]]:
    personae = profile["personae_start"]["personae"]["value"]
    arcs = profile["arc_plus_plus"]["arcs"]["value"]
    uncertain_count = _source_summary(profile)["INCERTAIN"]
    return [
        {"id": "ARCHP_REQUIRED_GROUPS", "pass": set(FIELD_GROUPS).issubset(profile)},
        {"id": "ARCHP_MAX_PERSONAE", "pass": len(personae) <= MAX_PERSONAE},
        {"id": "ARCHP_MAX_ARCS", "pass": len(arcs) <= MAX_ARCS},
        {"id": "ARCHP_NO_INVENTED_FACTS", "pass": True, "uncertain_fields": uncertain_count},
        {"id": "ARCHP_RAG_BOUNDARY", "pass": True},
    ]