"""Answer checking: normalized matching + keyword overlap (accepts paraphrases).

Correct if ANY of:
- exact normalized match,
- normalized answer contains normalized user text or vice versa (substring),
- token overlap: >= 60% of the answer's content tokens appear in the response.
"""
from __future__ import annotations

import re
import unicodedata

from .extract import STOPWORDS

_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def tokens(text: str) -> set[str]:
    return {t for t in normalize(text).split() if t not in STOPWORDS and len(t) > 1}


def check(user_answer: str, correct_answer: str) -> bool:
    u, c = normalize(user_answer), normalize(correct_answer)
    if not u or not c:
        return False
    if u == c:
        return True
    if u in c or c in u:
        return True
    u_tok, c_tok = tokens(user_answer), tokens(correct_answer)
    if not c_tok:
        return True
    return len(u_tok & c_tok) / len(c_tok) >= 0.6
