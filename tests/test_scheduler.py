import time

import pytest

from studysprint.scheduler import Scheduler


@pytest.fixture()
def sched(tmp_path):
    s = Scheduler(str(tmp_path / "cards.db"))
    yield s
    s.close()


def add_one(sched):
    sched.add_questions([{
        "type": "fill", "question": "Mitochondria are _____ of the cell.",
        "answer": "powerhouse", "hint": "", "explanation": "", "source": "",
    }])
    return sched.all_cards()[0]


def test_due_logic_new_cards_are_due(sched):
    card = add_one(sched)
    due = sched.due_cards()
    assert any(c.id == card.id for c in due)


def test_correct_grows_interval(sched):
    card = add_one(sched)
    c1 = sched.record_answer(card.id, True)
    assert c1.interval == 1.0
    # simulate the next day: jump due back to now, answer correctly again
    sched._conn.execute("UPDATE cards SET due_ts=? WHERE id=?",
                        (time.time() - 1, card.id))
    c2 = sched.record_answer(card.id, True)
    assert c2.interval == 6.0
    assert c2.due > time.time()  # not due anymore
    assert card.id not in [c.id for c in sched.due_cards()]


def test_wrong_resets_to_due_now(sched):
    card = add_one(sched)
    c1 = sched.record_answer(card.id, True)
    assert c1.interval == 1.0
    c2 = sched.record_answer(card.id, False)
    assert c2.interval == 0.0
    assert c2.repetitions == 0
    due = sched.due_cards()
    assert any(c.id == card.id for c in due)


def test_stats_accuracy(sched):
    card = add_one(sched)
    sched.record_answer(card.id, True)
    sched.record_answer(card.id, False)
    st = sched.stats()
    assert st["cards"] == 1
    assert st["total_answers"] == 2
    assert st["accuracy"] == pytest.approx(50.0)
