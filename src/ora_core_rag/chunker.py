"""Deterministic source chunking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Chunk:
    index: int
    heading: str
    text: str


def _split_markdown_sections(text: str) -> Iterable[tuple[str, list[str]]]:
    heading = "root"
    buffer: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("#"):
            if buffer:
                yield heading, buffer
            heading = line.strip("# ") or "section"
            buffer = [line]
        else:
            buffer.append(line)

    if buffer:
        yield heading, buffer


def chunk_text(text: str, *, kind: str = "unknown", max_chars: int = 1600) -> list[Chunk]:
    """Chunk text while preserving section headings when possible."""

    if not text.strip():
        return []

    if kind == "markdown":
        sections = list(_split_markdown_sections(text))
    else:
        sections = [("root", text.splitlines())]

    chunks: list[Chunk] = []
    current: list[str] = []
    current_heading = "root"

    def flush() -> None:
        nonlocal current
        body = "\n".join(line for line in current).strip()
        if body:
            chunks.append(Chunk(index=len(chunks), heading=current_heading, text=body))
        current = []

    for heading, lines in sections:
        section_text = "\n".join(lines).strip()
        if not section_text:
            continue

        if len(section_text) > max_chars:
            flush()
            current_heading = heading
            words = section_text.split()
            piece: list[str] = []
            for word in words:
                candidate = " ".join(piece + [word])
                if len(candidate) > max_chars and piece:
                    chunks.append(Chunk(index=len(chunks), heading=heading, text=" ".join(piece)))
                    piece = [word]
                else:
                    piece.append(word)
            if piece:
                chunks.append(Chunk(index=len(chunks), heading=heading, text=" ".join(piece)))
            continue

        candidate_len = len("\n".join(current + [section_text]))
        if current and candidate_len > max_chars:
            flush()

        current_heading = heading
        current.append(section_text)

    flush()
    return chunks
