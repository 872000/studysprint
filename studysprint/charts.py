"""Progress charts (matplotlib): accuracy over time, due questions, study time."""
from __future__ import annotations

import datetime
import os


def _mpl():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def accuracy_over_time(events: list[tuple[float, int]], out_path: str) -> str:
    """events: [(timestamp, correct(1/0))]; rolling accuracy curve."""
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if events:
        cum_c, cum_n, xs, ys = 0, 0, [], []
        for ts, c in sorted(events):
            cum_c += c
            cum_n += 1
            xs.append(datetime.datetime.fromtimestamp(ts))
            ys.append(cum_c / cum_n * 100.0)
        ax.plot(xs, ys, marker="o", linewidth=2, color="#2563eb")
        ax.axhline(100, color="#94a3b8", linestyle="--", linewidth=1)
        ax.set_ylim(0, 105)
    else:
        ax.text(0.5, 0.5, "No answers yet — run a quiz!", ha="center", va="center")
    ax.set_title("Answer Accuracy Over Time")
    ax.set_ylabel("Cumulative accuracy (%)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def questions_due(due_now: int, total: int, out_path: str) -> str:
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    remaining = max(total - due_now, 0)
    ax.bar(["Due now", "Not due"], [due_now, remaining], color=["#ef4444", "#22c55e"])
    for i, v in enumerate([due_now, remaining]):
        ax.text(i, v + 0.1, str(v), ha="center", fontweight="bold")
    ax.set_title("Spaced-Repetition Queue")
    ax.set_ylabel("Questions")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def study_time_bars(sessions: list[dict], out_path: str) -> str:
    """sessions: [{'started_ts', 'duration_s', 'kind'}]; minutes per day."""
    plt = _mpl()
    from collections import defaultdict

    per_day: dict[str, float] = defaultdict(float)
    for s in sessions:
        day = datetime.datetime.fromtimestamp(s["started_ts"]).strftime("%m-%d")
        per_day[day] += s.get("duration_s", 0) / 60.0
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if per_day:
        days = sorted(per_day)
        ax.bar(days, [per_day[d] for d in days], color="#8b5cf6")
        ax.set_ylabel("Minutes")
    else:
        ax.text(0.5, 0.5, "No sessions logged yet — try a pomodoro!", ha="center", va="center")
    ax.set_title("Study Time per Day")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def make_all(stats: dict, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = [
        accuracy_over_time(stats["answer_events"],
                           os.path.join(out_dir, "accuracy.png")),
        questions_due(stats["due"], stats["cards"],
                      os.path.join(out_dir, "due.png")),
        study_time_bars(stats["sessions"],
                        os.path.join(out_dir, "study_time.png")),
    ]
    return paths
