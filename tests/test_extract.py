import os

import pytest

from studysprint import extract, ingest

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "samples", "biology.md")


def sentences():
    return ingest.load_notes(SAMPLE)


def test_ingest_strips_markdown_and_splits():
    sents = sentences()
    assert len(sents) >= 10
    for s in sents:
        assert "**" not in s and "#" not in s
        assert s[0].isupper() or s[0].isdigit()


def test_extract_picks_nontrivial_sentences():
    sents = sentences()
    keys = extract.extract_key_sentences(sents, top_k=5)
    assert len(keys) == 5
    joined = " ".join(keys).lower()
    # key sentences should mention real domain terms, not be generic
    assert any(term in joined for term in
              ["mitochondria", "photosynthesis", "nucleus", "osmosis", "enzyme"])


def test_extract_scores_rank_content():
    sents = [
        "The thing is stuff and things about the thing.",
        "Mitochondria produce ATP through cellular respiration in the powerhouse.",
    ]
    scored = extract.score_sentences(sents)
    assert scored[0][0].startswith("Mitochondria")
