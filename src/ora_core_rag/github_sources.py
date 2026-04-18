"""GitHub source discovery for ORA_CORE_RAG."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_EXTENSIONS = (
    ".md",
    ".json",
    ".txt",
    ".py",
    ".ps1",
    ".psm1",
    ".gpl",
    ".gpv2",
)

KIND_BY_EXTENSION = {
    ".md": "markdown",
    ".json": "json",
    ".txt": "text",
    ".py": "python",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".gpl": "text",
    ".gpv2": "text",
}


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def source_from_tree_item(
    *,
    repo: str,
    ref: str,
    item: dict[str, Any],
    canon_level: str = "RUNTIME",
    tags: list[str] | None = None,
) -> dict[str, Any] | None:
    if item.get("type") != "blob":
        return None

    path = str(item.get("path", ""))
    lower_path = path.lower()
    extension = next((ext for ext in DEFAULT_EXTENSIONS if lower_path.endswith(ext)), "")
    if not extension:
        return None

    encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    uri = f"https://raw.githubusercontent.com/{repo}/{urllib.parse.quote(ref, safe='')}/{encoded_path}"
    source_id = _safe_id(f"{repo}_{ref}_{path}")

    return {
        "id": source_id,
        "uri": uri,
        "kind": KIND_BY_EXTENSION.get(extension, "unknown"),
        "scope": "ORA_CORE",
        "canon_level": canon_level,
        "title": path,
        "tags": list(tags or []) + ["github", repo.replace("/", "_")],
    }


def sources_from_tree(
    *,
    repo: str,
    ref: str,
    tree_items: list[dict[str, Any]],
    canon_level: str = "RUNTIME",
    tags: list[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for item in tree_items:
        source = source_from_tree_item(repo=repo, ref=ref, item=item, canon_level=canon_level, tags=tags)
        if source:
            sources.append(source)
            if limit is not None and len(sources) >= limit:
                break
    return sources


class GitHubSourceDiscovery:
    """Discover indexable source files from public GitHub repositories."""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def fetch_tree(self, repo: str, ref: str = "main") -> list[dict[str, Any]]:
        encoded_ref = urllib.parse.quote(ref, safe="")
        url = f"https://api.github.com/repos/{repo}/git/trees/{encoded_ref}?recursive=1"
        request = urllib.request.Request(url, headers={"User-Agent": "ORA_CORE_RAG/0.2"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        tree = data.get("tree")
        if not isinstance(tree, list):
            raise ValueError(f"GitHub tree response for {repo}@{ref} is invalid.")
        return tree

    def discover(
        self,
        repo: str,
        *,
        ref: str = "main",
        canon_level: str = "RUNTIME",
        tags: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        tree = self.fetch_tree(repo, ref=ref)
        return sources_from_tree(repo=repo, ref=ref, tree_items=tree, canon_level=canon_level, tags=tags, limit=limit)

    def manifest(
        self,
        repo: str,
        *,
        ref: str = "main",
        canon_level: str = "RUNTIME",
        tags: list[str] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return {
            "version": "1.0.0",
            "sources": self.discover(repo, ref=ref, canon_level=canon_level, tags=tags, limit=limit),
        }
