"""Turn an article into cognitive-anchor slots without fixed-width chunking."""

from __future__ import annotations

import re
from typing import Any

from .errors import IPPicError


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SENTENCE_END = re.compile(r"(?<=[。！？!?])")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _headline(value: str) -> str:
    text = _clean(value)
    first = SENTENCE_END.split(text, maxsplit=1)[0].strip()
    return (first or text)[:32]


def _points(value: str) -> list[str]:
    parts = [
        _clean(part)
        for part in re.split(r"[。！？!?；;]\s*", value)
        if _clean(part)
    ]
    return [part[:32] for part in parts[:4]]


def _heading_sections(article: str) -> tuple[str, list[tuple[int, str, str]]]:
    title = ""
    sections: list[tuple[int, str, list[str]]] = []
    current: tuple[int, str, list[str]] | None = None
    preface: list[str] = []
    for raw_line in article.splitlines():
        line = raw_line.strip()
        match = HEADING.match(line)
        if match:
            if current is not None:
                sections.append(current)
            level = len(match.group(1))
            heading = _clean(match.group(2))
            if level == 1 and not title:
                title = heading
                current = None
            else:
                current = (level, heading, [])
            continue
        if not line:
            continue
        if current is None:
            preface.append(line)
        else:
            current[2].append(line)
    if current is not None:
        sections.append(current)
    normalized = [
        (level, heading, _clean(" ".join(body)))
        for level, heading, body in sections
    ]
    if not normalized and preface:
        return title, []
    return title, normalized


def _paragraph_anchors(article: str) -> list[tuple[str, str]]:
    paragraphs = [
        _clean(part)
        for part in re.split(r"\n\s*\n+", article)
        if _clean(part) and not HEADING.match(part.strip())
    ]
    if len(paragraphs) <= 1:
        return [(_headline(article), _clean(article))]
    return [(_headline(part), part) for part in paragraphs]


def plan_article_slots(article: str) -> list[dict[str, Any]]:
    """Return 1 short-form slot or 4-8 long-form semantic anchor slots."""

    text = str(article or "").strip()
    if not text:
        raise IPPicError("article content cannot be empty")
    title, sections = _heading_sections(text)
    anchors: list[tuple[str, str]]
    if sections:
        anchors = [(heading, body or heading) for _, heading, body in sections]
    else:
        anchors = _paragraph_anchors(text)
    # A short article is one judgment. Long articles retain explicit semantic
    # boundaries; no character-count slicing is used.
    if len(anchors) < 4:
        anchors = [(_headline(title or text), _clean(text))]
    else:
        anchors = anchors[:8]
    result = []
    for index, (headline, body) in enumerate(anchors, 1):
        result.append(
            {
                "id": f"article-slot-{index:02d}",
                "content_outline": {
                    "headline": _headline(headline),
                    "summary": body[:72],
                    "points": _points(body),
                },
                "source": {
                    "selection_basis": "cognitive-anchor",
                    "source_excerpt": body[:160],
                },
            }
        )
    return result
