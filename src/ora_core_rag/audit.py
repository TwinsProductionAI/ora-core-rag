"""JSONL audit logging for ORA_CORE_RAG."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .hashing import sha256_json


class AuditLogger:
    """Append-only JSONL audit logger.

    The logger stores routing and retrieval metadata only. It should not be used
    for raw client payload persistence.
    """

    def __init__(self, path: str | Path | None):
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        event["event_hash"] = sha256_json(event)

        if self.path:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")

        return event
