"""StudySprint CLI.

Commands:
  studysprint ingest <notes.md> [--top N]   Extract key sentences, generate
                                             questions, store in the card deck.
  studysprint quiz [--n N]                   Quiz on N random cards.
  studysprint review [--n N]                 Review N due cards (spaced repetition).
  studysprint pomodoro <minutes>             Focus timer with countdown + logging.
  studysprint charts                         Render progress charts to assets/.
  studysprint stats                          Show deck stats.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time

DEFAULT_DB = os.path.expanduser("~/.studysprint/cards.db")


def _sched(db_path: str):
    from .scheduler import Scheduler

    return Scheduler(db_path)


def cmd_ingest(args) -> int:
    from . import extract, ingest, questions

    if os.path.isdir(args.path):
        sentences = ingest.load_directory(args.path)
    else:
        sentences = ingest.load_notes(args.path)
    print(f"📄 Loaded {len(sentences)} sentences from {args.path}")
    keys = extract.extract_key_sentences(sentences, top_k=args.top)
    print(f"⭐ Extracted {len(keys)} key sentences")
    rng = random.Random(42)
    qs: list[dict] = []
    for s in keys:
        qs.extend(questions.generate(s, rng))
    sched = _sched(args.db)
    added = sched.add_questions(qs)
    sched.close()
    print(f"❓ Generated {len(qs)} questions → deck now holds {added} new cards")
    return 0


def cmd_quiz(args) -> int:
    from . import quiz

    sched = _sched(args.db)
    cards = sched.all_cards()
    if not cards:
        print("Deck is empty. Run: studysprint ingest samples/")
        return 1
    sample = random.sample(cards, min(args.n, len(cards)))
    quiz.run_quiz(sample, sched)
    sched.close()
    return 0


def cmd_review(args) -> int:
    from . import quiz

    sched = _sched(args.db)
    due = sched.due_cards(limit=args.n)
    if not due:
        print("🎉 Nothing due! Your memory is fresh.")
        return 0
    print(f"🔁 {len(due)} card(s) due for review")
    quiz.run_quiz(due, sched)
    sched.close()
    return 0


def cmd_pomodoro(args) -> int:
    from . import pomodoro

    sched = _sched(args.db)
    pomodoro.run(args.minutes, scheduler=sched, label=args.label)
    sched.close()
    return 0


def cmd_charts(args) -> int:
    from . import charts

    sched = _sched(args.db)
    stats = sched.stats()
    sched.close()
    paths = charts.make_all(stats, args.out)
    print("📊 Charts written:")
    for p in paths:
        print("   ", p)
    return 0


def cmd_stats(args) -> int:
    sched = _sched(args.db)
    st = sched.stats()
    sched.close()
    print(f"🃏 Cards: {st['cards']}")
    print(f"⏰ Due now: {st['due']}")
    print(f"✅ Answered: {st['total_answers']}  (correct: {st['total_correct']})")
    print(f"🎯 Accuracy: {st['accuracy']:.1f}%")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="studysprint",
                                description="StudySprint — turn notes into quizzes.")
    p.add_argument("--db", default=DEFAULT_DB, help="SQLite deck path")
    sub = p.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest", help="Build a question deck from notes")
    ing.add_argument("path", help="Notes .md/.txt file or directory")
    ing.add_argument("--top", type=int, default=10, help="Key sentences to extract")
    ing.set_defaults(func=cmd_ingest)

    qz = sub.add_parser("quiz", help="Quiz yourself on random cards")
    qz.add_argument("--n", type=int, default=10)
    qz.set_defaults(func=cmd_quiz)

    rv = sub.add_parser("review", help="Spaced-repetition review of due cards")
    rv.add_argument("--n", type=int, default=20)
    rv.set_defaults(func=cmd_review)

    pm = sub.add_parser("pomodoro", help="Focus timer")
    pm.add_argument("minutes", type=int, nargs="?", default=25)
    pm.add_argument("--label", default="Focus")
    pm.set_defaults(func=cmd_pomodoro)

    ch = sub.add_parser("charts", help="Render progress charts")
    ch.add_argument("--out", default="assets",
                    help="Output directory for PNG charts")
    ch.set_defaults(func=cmd_charts)

    st = sub.add_parser("stats", help="Show deck stats")
    st.set_defaults(func=cmd_stats)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
