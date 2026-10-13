from __future__ import annotations


def clamp_text(text: str, limit: int) -> str:
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip() + "\n\n[Текст обрезан из-за ограничения размера запроса.]"


def split_for_telegram(text: str, limit: int = 3900) -> list[str]:
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    buffer = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= limit:
            buffer = candidate
            continue
        if buffer:
            parts.append(buffer)
            buffer = ""
        while len(paragraph) > limit:
            parts.append(paragraph[:limit])
            paragraph = paragraph[limit:]
        buffer = paragraph
    if buffer:
        parts.append(buffer)
    return parts
