"""Quiz runner: asks questions, checks answers, scores, explains."""
from __future__ import annotations

import time

from . import checker


def ask(card, input_fn=input, print_fn=print) -> bool:
    print_fn(f"\n[{card.qtype}] {card.question}")
    if card.qtype == "truefalse":
        print_fn("(answer: true / false)")
    user = input_fn("Your answer: ").strip()
    ok = checker.check(user, card.answer)
    if ok:
        print_fn("✅ Correct!")
    else:
        print_fn(f"❌ Not quite. The answer is: {card.answer}")
    if card.hint and not ok:
        print_fn(f"💡 Hint: {card.hint}")
    print_fn(f"📝 {card.explanation}")
    return ok


def run_quiz(cards, scheduler, input_fn=input, print_fn=print) -> tuple[int, int]:
    correct = 0
    answered = 0
    start = time.time()
    for card in cards:
        answered += 1
        ok = ask(card, input_fn=input_fn, print_fn=print_fn)
        scheduler.record_answer(card.id, ok)
        if ok:
            correct += 1
    duration = int(time.time() - start)
    scheduler.log_session("quiz", started_ts=start, duration_s=duration,
                          answered=answered, correct=correct)
    if answered:
        print_fn(f"\n🏁 Score: {correct}/{answered} ({correct / answered * 100:.0f}%)")
    return answered, correct
