"""Question generation from key sentences via hand-built templates.

Types:
- fill-in-the-blank: mask the highest-scoring "key term" (rarest non-stopword) in the
  sentence with `_____`.
- true/false: produce a TRUE variant (the sentence itself) and a FALSE variant by
  negating/altering a fact (swap a key term with a plausible distractor or negate
  the verb).
- wh-question: heuristic transforms for "What/Which/Why/How many/When" based on
  sentence patterns.
"""
from __future__ import annotations

import random
import re

from . import extract

KeyTerm = str


def key_term(sentence: str) -> KeyTerm:
    """Pick the most "specific" term: rarest long non-stopword; fallback first noun-ish."""
    words = extract._content_words(sentence)
    if not words:
        return ""
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    # rarity within sentence + length => specificity
    return max(words, key=lambda w: (1.0 / counts[w], len(w), -words.index(w)))


def _mask_term(sentence: str, term: str) -> str:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub("_____", sentence, count=1)


def make_fill_blank(sentence: str) -> dict:
    term = key_term(sentence)
    if not term:
        return {}
    return {
        "type": "fill",
        "question": _mask_term(sentence, term) + " (fill in the blank)",
        "answer": term,
        "hint": f"The answer starts with '{term[0]}' and has {len(term)} letters.",
        "explanation": f"The key term is '{term}'. Sentence: {sentence}",
    }


_NEGATIONS = [
    (r"\bis\b", "is not"),
    (r"\bare\b", "are not"),
    (r"\bwas\b", "was not"),
    (r"\bwere\b", "were not"),
    (r"\bhas\b", "does not have"),
    (r"\bhave\b", "do not have"),
    (r"\bcan\b", "cannot"),
]


def _negate(sentence: str) -> str:
    for pattern, replacement in _NEGATIONS:
        new = re.sub(pattern, replacement, sentence, count=1)
        if new != sentence:
            return new
    return sentence


def _distractor_terms(sentence: str) -> list[str]:
    pool = [
        "water", "oxygen", "carbon", "energy", "heat", "light", "metal", "Europe",
        "Asia", "Africa", "1914", "1789", "1492", "gold", "silver", "sodium",
        "chlorine", "the cell", "the nucleus", "the mitochondria", "a king",
        "the army", "the treaty", "the emperor",
    ]
    ours = set(extract._words(sentence))
    return [p for p in pool if p.lower() not in ours]


def make_true_false(sentence: str, rng: random.Random) -> dict:
    if rng.random() < 0.5:
        return {
            "type": "truefalse",
            "question": f"True or False: {sentence}",
            "answer": "true",
            "hint": "Consider the key term of the sentence.",
            "explanation": f"True — the sentence is correct as written: {sentence}",
        }
    false_stmt = _negate(sentence)
    if false_stmt == sentence:
        # fall back to term-swap with a distractor
        term = key_term(sentence)
        distractors = _distractor_terms(sentence)
        if term and distractors:
            d = rng.choice(distractors)
            false_stmt = _mask_term(sentence, term).replace("_____", d)
    return {
        "type": "truefalse",
        "question": f"True or False: {false_stmt}",
        "answer": "false",
        "hint": "Look for the altered fact.",
        "explanation": f"False — the original sentence is: {sentence}",
    }


_WH_PATTERNS = [
    (re.compile(r"^(.*?)\s+is\s+(called|known as|defined as)\s+(.*)$", re.I),
     lambda m: ("What", f"What {m.group(1).strip()} is {m.group(2)}?", m.group(3))),
    (re.compile(r"^(.*?)\s+(contains?|includes?|consists of)\s+(.*)$", re.I),
     lambda m: ("What", f"What does {m.group(1).strip()} contain?", m.group(3))),
    (re.compile(r"^(In \d{3,4}|On \w+ \d{1,2},? \d{3,4}|\d{3,4}),?\s+(.*)$"),
     lambda m: ("When", f"When did this happen: {m.group(2).strip()}?",
                re.search(r"\d{3,4}", m.group(1)).group())),
    (re.compile(r"^(.*?)\s+(caused|led to|resulted in)\s+(.*)$", re.I),
     lambda m: ("Why", f"What did {m.group(1).strip()} cause?", m.group(3))),
    (re.compile(r"^(.*?)\s+(has|have)\s+(\d+)\s+(.*)$", re.I),
     lambda m: ("How many", f"How many {m.group(4).strip()} does {m.group(1).strip()} have?", m.group(3))),
]


def make_wh(sentence: str) -> dict:
    for pattern, builder in _WH_PATTERNS:
        m = pattern.match(sentence.strip())
        if m:
            kind, q, a = builder(m)
            answer = a.strip().rstrip(".")
            return {
                "type": "wh",
                "question": q,
                "answer": answer,
                "hint": f"A {kind.lower()} question — the answer is a phrase from your notes.",
                "explanation": f"From your notes: {sentence}",
            }
    return {}


def generate(sentence: str, rng: random.Random | None = None) -> list[dict]:
    rng = rng or random.Random()
    out: list[dict] = []
    fb = make_fill_blank(sentence)
    if fb:
        out.append(fb)
    out.append(make_true_false(sentence, rng))
    wh = make_wh(sentence)
    if wh:
        out.append(wh)
    for q in out:
        q["source"] = sentence
    return out
