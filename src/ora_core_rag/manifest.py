"""Source manifest and source loading utilities."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

CORE_SCOPE = "ORA_CORE"


class ManifestError(ValueError):
    """Raised when a source manifest is invalid."""


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be a JSON object.")
    return data


def validate_source(source: dict[str, Any]) -> dict[str, Any]:
    source_id = str(source.get("id", "")).strip()
    uri = str(source.get("uri", "")).strip()
    scope = str(source.get("scope", "")).strip()

    if not source_id:
        raise ManifestError("Source is missing id.")
    if not uri:
        raise ManifestError(f"Source {source_id} is missing uri.")
    if scope != CORE_SCOPE:
        raise ManifestError(f"Source {source_id} has forbidden scope {scope!r}; expected ORA_CORE.")

    normalized = dict(source)
    normalized.setdefault("kind", "unknown")
    normalized.setdefault("canon_level", "CORE")
    normalized.setdefault("title", source_id)
    normalized.setdefault("tags", [])
    return normalized


def load_source_manifest(path: str | Path) -> list[dict[str, Any]]:
    data = load_json(path)
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ManifestError("Manifest requires a non-empty sources array.")
    return [validate_source(item) for item in sources]


def read_uri(uri: str, *, base_dir: str | Path | None = None, timeout: int = 20) -> str:
    if uri.startswith("http://") or uri.startswith("https://"):
        request = urllib.request.Request(uri, headers={"User-Agent": "ORA_CORE_RAG/0.1"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8-sig")

    path = Path(uri)
    if not path.is_absolute() and base_dir is not None:
        path = Path(base_dir) / path
    return path.read_text(encoding="utf-8-sig")
