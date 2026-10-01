import io
from contextlib import redirect_stdout

import pytest

from studysprint import pomodoro
from studysprint.scheduler import Scheduler


def test_pomodoro_completes_and_logs(tmp_path):
    sched = Scheduler(str(tmp_path / "cards.db"))
    buf = io.StringIO()
    # 0.05 min -> 3 countdown ticks; use tiny tick to run fast
    with redirect_stdout(buf):
        completed = pomodoro.run(0.05, scheduler=sched, tick=0.001)
    sched.close()
    assert completed == 3
    out = buf.getvalue()
    assert "Pomodoro" in out and "Time!" in out
    fresh = Scheduler(str(tmp_path / "cards.db"))
    sessions = fresh.stats()["sessions"]
    fresh.close()
    assert len(sessions) == 1
    assert sessions[0]["kind"] == "pomodoro"


def test_pomodoro_rejects_bad_minutes():
    with pytest.raises(ValueError):
        pomodoro.run(0)
