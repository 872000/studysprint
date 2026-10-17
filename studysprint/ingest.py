"""Notes ingestion: read markdown/text files, strip markdown syntax, split sentences."""
from __future__ import annotations

import os
import re

_HEADING_RE = re.compile(r"^#{1,6}\s*")
_LI_RE = re.compile(r"^\s*[-*+]\s+")
_NUM_LI_RE = re.compile(r"^\s*\d+[.)]\s+")
_CODE_FENCE = "```"
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_EMPHASIS = re.compile(r"(\*\*|__)(.*?)\1")
_EMPHASIS2 = re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
_URL_RE = re.compile(r"https?://\S+")


def clean_line(line: str) -> str:
    """Strip markdown syntax from one line, keeping its plain text."""
    line = line.strip()
    if line.startswith(_CODE_FENCE):
        return ""
    line = _IMAGE_RE.sub("", line)
    line = _LINK_RE.sub(r"\1", line)
    line = _INLINE_CODE.sub(r"\1", line)
    line = _EMPHASIS.sub(r"\2", line)
    line = _EMPHASIS2.sub(r"\1", line)
    line = _URL_RE.sub("", line)
    line = _HEADING_RE.sub("", line)
    line = _LI_RE.sub("", line)
    line = _NUM_LI_RE.sub("", line)
    return line.strip()


def split_sentences(text: str) -> list[str]:
    """Split plain text into sentences, keeping abbreviations safe."""
    abbrev = re.compile(r"\b(e\.g|i\.e|Dr|Mr|Mrs|Ms|St|vs|etc|Fig|No)\.$", re.I)
    raw = _SENT_SPLIT.split(text.replace("\n", " "))
    out: list[str] = []
    buf = ""
    for piece in raw:
        piece = piece.strip()
        if not piece:
            continue
        buf = (buf + " " + piece).strip() if buf else piece
        if abbrev.search(buf):
            continue
        out.append(buf)
        buf = ""
    if buf:
        out.append(buf)
    return [s for s in out if len(s.split()) >= 3]


def load_notes(path: str) -> list[str]:
    """Load a markdown/text file and return a list of clean sentences."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Notes file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    # drop fenced code blocks
    blocks: list[str] = []
    in_fence = False
    for line in raw.splitlines():
        if line.strip().startswith(_CODE_FENCE):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        blocks.append(line)
    cleaned = [clean_line(l) for l in blocks]
    text = " ".join(c for c in cleaned if c)
    return split_sentences(text)


def load_directory(path: str) -> list[str]:
    """Load every .md/.txt file in a directory and return clean sentences."""
    sentences: list[str] = []
    for name in sorted(os.listdir(path)):
        if name.lower().endswith((".md", ".txt")):
            sentences.extend(load_notes(os.path.join(path, name)))
    return sentences
