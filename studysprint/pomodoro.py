"""Pomodoro timer CLI with console countdown and session logging."""
from __future__ import annotations

import sys
import time


def _fmt(seconds: int) -> str:
    m, s = divmod(max(seconds, 0), 60)
    return f"{m:02d}:{s:02d}"


def run(minutes: int = 25, scheduler=None, label: str = "Focus", tick: float = 1.0) -> int:
    """Run a pomodoro of `minutes` minutes, printing a console countdown.

    Returns the completed seconds (== minutes*60 on a clean run).
    `tick` scales real seconds per countdown second (use small tick in tests).
    """
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    total = int(minutes * 60)
    print(f"\n🍅 Pomodoro: {label} — {minutes} min. Ctrl+C to stop.\n")
    start = time.time()
    try:
        remaining = total
        while remaining > 0:
            sys.stdout.write(f"\r  ⏳ {_fmt(remaining)} remaining")
            sys.stdout.flush()
            time.sleep(tick)
            remaining -= 1
        print("\n\n✅ Time! Take a break.\n")
        completed = int(minutes * 60)
    except KeyboardInterrupt:
        print("\n\n⏸️  Stopped early.\n")
        completed = int(time.time() - start)
    if scheduler is not None:
        scheduler.log_session(
            "pomodoro", started_ts=start, duration_s=completed, answered=0, correct=0
        )
        scheduler.log_pomodoro(minutes if completed >= int(minutes * 60) else 0)
    return completed
