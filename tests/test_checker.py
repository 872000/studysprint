import pytest

from studysprint import checker


def test_exact_match():
    assert checker.check("ATP", "ATP")


def test_case_and_punctuation_insensitive():
    assert checker.check("the powerhouse of the cell!", "Powerhouse of the Cell")


def test_accepts_paraphrase_subset():
    # paraphrase containing most of the answer's content words
    assert checker.check("it makes ATP during cellular respiration",
                         "they produce ATP through cellular respiration")


def test_substring_match():
    assert checker.check("Bastille", "the Storming of the Bastille")


def test_rejects_wrong_answer():
    assert not checker.check("Paris", "London")
    assert not checker.check("water", "ATP")


def test_rejects_empty():
    assert not checker.check("", "ATP")
    assert not checker.check("ATP", "")


def test_true_false_matching():
    assert checker.check("True", "true")
    assert not checker.check("true", "false")
