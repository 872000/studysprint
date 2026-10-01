"""Key-sentence extraction: frequency-based scoring written from scratch.

Technique: normalized TF (term frequency with max-count normalization) summed over
the sentence's words, weighted by sentence position (early sentences get a small
boost, mirroring how notes introduce key ideas first), minus a penalty for very
long sentences. Stopwords are a local list — no external NLP libraries.
"""
from __future__ import annotations

import math
from collections import Counter

from . import ingest

STOPWORDS = frozenset("""
a an the and or but if then else when while of at by for with about into through
during before after above below to from up down in out on off over under again
further once here there all any both each few more most other some such no nor
not only own same so than too very can will just should now is are was were be
been being have has had having do does did doing would could ought i'm you he
she it we they them his her its our their this that these those am i me my we
us your yours him himself herself itself ourselves themselves what which who
whom whose how why where when because until against between among per via
as also within without may might must shall cannot can't don't doesn't didn't
won't wouldn't shouldn't couldn't isn't aren't wasn't weren't it's that's there's
here's
""".split())


def _words(sentence: str) -> list[str]:
    return [w.lower() for w in _TOKEN_RE.findall(sentence)]


_TOKEN_RE = __import__("re").compile(r"[A-Za-z][A-Za-z'\-]*")


def _content_words(sentence: str) -> list[str]:
    return [w for w in _words(sentence) if w not in STOPWORDS and len(w) > 2]


def score_sentences(sentences: list[str]) -> list[tuple[str, float]]:
    """Return (sentence, score) pairs, highest score first."""
    if not sentences:
        return []
    doc_freq: Counter = Counter()
    content: list[list[str]] = []
    for s in sentences:
        cw = _content_words(s)
        content.append(cw)
        doc_freq.update(set(cw))
    n = len(sentences)
    idf = {w: math.log((n + 1) / (df + 1)) + 1.0 for w, df in doc_freq.items()}
    scored: list[tuple[str, float]] = []
    for idx, (s, cw) in enumerate(zip(sentences, content)):
        if not cw:
            continue
        counts = Counter(cw)
        max_count = max(counts.values())
        # normalized TF-IDF sum over sentence terms
        score = sum((counts[w] / max_count) * idf[w] for w in counts)
        # position boost: earlier sentences matter a bit more
        score *= 1.0 + 0.25 * (1.0 - idx / max(n, 1))
        # mild length penalty past ~25 words
        wc = len(s.split())
        if wc > 25:
            score *= 25.0 / wc
        scored.append((s, score))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


def extract_key_sentences(sentences: list[str], top_k: int = 10) -> list[str]:
    scored = score_sentences(sentences)
    return [s for s, _ in scored[:top_k]]
