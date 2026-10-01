import pytest

from studysprint import quiz
from studysprint.scheduler import Scheduler


@pytest.fixture()
def sched(tmp_path):
    s = Scheduler(str(tmp_path / "cards.db"))
    yield s
    s.close()


def _cards(sched):
    sched.add_questions([
        {"type": "fill", "question": "Q1: mitochondria are _____",
         "answer": "powerhouse", "hint": "starts with p",
         "explanation": "E1", "source": "S1"},
        {"type": "truefalse", "question": "True or False: water is wet",
         "answer": "true", "hint": "", "explanation": "E2", "source": "S2"},
    ])
    return sched.all_cards()


def test_quiz_scoring_all_correct(sched):
    cards = _cards(sched)
    answers = iter(["powerhouse", "true"])
    answered, correct = quiz.run_quiz(
        cards, sched,
        input_fn=lambda _prompt: next(answers),
        print_fn=lambda *a: None,
    )
    assert (answered, correct) == (2, 2)


def test_quiz_scoring_wrong_answers_recorded(sched):
    cards = _cards(sched)
    answers = iter(["banana", "false"])
    answered, correct = quiz.run_quiz(
        cards, sched,
        input_fn=lambda _prompt: next(answers),
        print_fn=lambda *a: None,
    )
    assert (answered, correct) == (2, 0)
    st = sched.stats()
    assert st["total_answers"] == 2
    assert st["accuracy"] == pytest.approx(0.0)


def test_quiz_explains_and_hints_on_wrong(sched):
    cards = _cards(sched)
    shown = []
    answered, correct = quiz.run_quiz(
        cards[:1], sched,
        input_fn=lambda _prompt: "nope",
        print_fn=lambda *a: shown.append(" ".join(str(x) for x in a)),
    )
    assert correct == 0
    text = "\n".join(shown)
    assert "powerhouse" in text          # explanation shows answer
    assert "starts with p" in text       # hint shown on wrong answer
