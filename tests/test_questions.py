import random

import pytest

from studysprint import questions

S1 = "Mitochondria are known as the powerhouse of the cell because they produce ATP."
S2 = "In 1789, the Storming of the Bastille marked the beginning of the French Revolution."
S3 = "The cell is the basic structural and functional unit of all known living organisms."


def test_fill_blank_has_valid_answer():
    q = questions.make_fill_blank(S1)
    assert q["type"] == "fill"
    assert "_____" in q["question"]
    assert q["answer"].lower() in S1.lower()
    assert len(q["answer"]) > 2


def test_fill_blank_masks_answer_in_sentence():
    q = questions.make_fill_blank(S1)
    assert q["answer"] not in q["question"]


def test_true_false_variants_are_valid():
    rng = random.Random(1)
    seen = set()
    for _ in range(10):
        q = questions.make_true_false(S1, rng)
        seen.add(q["answer"])
        assert q["answer"] in ("true", "false")
        assert q["question"].startswith("True or False:")
    # over 10 draws with seed 1 we should see both variants
    assert seen == {"true", "false"}


def test_wh_question_has_answer_in_notes():
    q = questions.make_wh("The cell is defined as the basic unit of life.")
    assert q  # non-empty dict
    assert q["answer"].lower() in "The cell is defined as the basic unit of life.".lower()


def test_wh_year_pattern():
    q = questions.make_wh(S2)
    assert q["type"] == "wh"
    assert q["answer"] == "1789"


def test_generate_returns_multiple_types():
    rng = random.Random(7)
    qs = questions.generate(S1, rng)
    types = {q["type"] for q in qs}
    assert "fill" in types and "truefalse" in types
    for q in qs:
        assert q["answer"], "every question must have a non-empty answer"
        assert q["source"] == S1
