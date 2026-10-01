import os

import pytest

from studysprint import charts

EVENTS = [(1000.0, 1), (2000.0, 0), (3000.0, 1), (4000.0, 1)]


def make_stats(tmp_path):
    return {
        "cards": 10,
        "due": 3,
        "answer_events": EVENTS,
        "sessions": [
            {"started_ts": 1000.0, "duration_s": 1500, "kind": "pomodoro"},
            {"started_ts": 1000.0 + 86400, "duration_s": 600, "kind": "quiz"},
        ],
    }


def test_charts_render_pngs(tmp_path):
    stats = make_stats(tmp_path)
    out = str(tmp_path / "charts")
    paths = charts.make_all(stats, out)
    assert len(paths) == 3
    for p in paths:
        assert os.path.isfile(p)
        assert os.path.getsize(p) > 1000
        with open(p, "rb") as fh:
            assert fh.read(4) == b"\x89PNG"


def test_charts_empty_stats(tmp_path):
    stats = {"cards": 0, "due": 0, "answer_events": [], "sessions": []}
    paths = charts.make_all(stats, str(tmp_path / "c2"))
    for p in paths:
        assert os.path.isfile(p)
