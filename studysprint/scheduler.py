"""Spaced-repetition-lite scheduler backed by SQLite.

Per question: easiness (SM-2 style), interval in days, repetitions, next due date.
Correct -> interval grows (x e-factor, min 1d -> up to 30d). Wrong -> reset to
due-now with a small e-factor penalty.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass

DAY = 24 * 3600


@dataclass
class Card:
    id: int
    question: str
    answer: str
    qtype: str
    hint: str
    explanation: str
    source: str
    easiness: float
    interval: float
    repetitions: int
    due: float
    total: int
    correct: int


class Scheduler:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                qtype TEXT NOT NULL,
                hint TEXT DEFAULT '',
                explanation TEXT DEFAULT '',
                source TEXT DEFAULT '',
                easiness REAL DEFAULT 2.5,
                interval_days REAL DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                due_ts REAL DEFAULT 0,
                total INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,          -- 'quiz' | 'review' | 'pomodoro'
                started_ts REAL NOT NULL,
                duration_s INTEGER DEFAULT 0,
                answered INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                ts REAL NOT NULL,
                card_id INTEGER,
                kind TEXT NOT NULL,          -- 'answer' | 'pomodoro'
                correct INTEGER,
                detail TEXT DEFAULT ''
            );
            """
        )
        self._conn.commit()

    # ---------- cards ----------
    def add_questions(self, questions: list[dict]) -> int:
        now = time.time()
        rows = [
            (q["question"], q["answer"], q.get("type", ""), q.get("hint", ""),
             q.get("explanation", ""), q.get("source", ""), 2.5, 0.0, 0, now)
            for q in questions
        ]
        self._conn.executemany(
            "INSERT INTO cards (question, answer, qtype, hint, explanation, source,"
            " easiness, interval_days, repetitions, due_ts) VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        self._conn.commit()
        return self._conn.total_changes

    def _row_to_card(self, row: sqlite3.Row) -> Card:
        return Card(
            id=row["id"], question=row["question"], answer=row["answer"],
            qtype=row["qtype"], hint=row["hint"] or "",
            explanation=row["explanation"] or "", source=row["source"] or "",
            easiness=row["easiness"], interval=row["interval_days"],
            repetitions=row["repetitions"], due=row["due_ts"],
            total=row["total"], correct=row["correct"],
        )

    def due_cards(self, limit: int | None = None, now: float | None = None) -> list[Card]:
        now = time.time() if now is None else now
        sql = "SELECT * FROM cards WHERE due_ts <= ? ORDER BY due_ts ASC"
        params: tuple = (now,)
        if limit is not None:
            sql += " LIMIT ?"
            params = (now, limit)
        return [self._row_to_card(r) for r in self._conn.execute(sql, params)]

    def all_cards(self) -> list[Card]:
        return [self._row_to_card(r) for r in self._conn.execute("SELECT * FROM cards ORDER BY id")]

    def record_answer(self, card_id: int, correct: bool, now: float | None = None) -> Card:
        now = time.time() if now is None else now
        row = self._conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        card = self._row_to_card(row)
        if correct:
            card.repetitions += 1
            if card.repetitions == 1:
                card.interval = 1.0
            elif card.repetitions == 2:
                card.interval = 6.0
            else:
                card.interval = min(card.interval * card.easiness, 30.0)
            card.correct += 1
        else:
            card.repetitions = 0
            card.interval = 0.0  # due again now
            card.easiness = max(1.3, card.easiness - 0.2)
        card.total += 1
        card.due = now + card.interval * DAY
        self._conn.execute(
            "UPDATE cards SET easiness=?, interval_days=?, repetitions=?, due_ts=?,"
            " total=?, correct=? WHERE id=?",
            (card.easiness, card.interval, card.repetitions, card.due,
             card.total, card.correct, card.id),
        )
        self._conn.execute(
            "INSERT INTO events (ts, card_id, kind, correct) VALUES (?,?,?,?)",
            (now, card_id, "answer", 1 if correct else 0),
        )
        self._conn.commit()
        return card

    # ---------- sessions & stats ----------
    def log_session(self, kind: str, started_ts: float, duration_s: int,
                    answered: int = 0, correct: int = 0) -> None:
        self._conn.execute(
            "INSERT INTO sessions (kind, started_ts, duration_s, answered, correct)"
            " VALUES (?,?,?,?,?)",
            (kind, started_ts, duration_s, answered, correct),
        )
        self._conn.commit()

    def log_pomodoro(self, minutes: int, now: float | None = None) -> None:
        now = time.time() if now is None else now
        self._conn.execute(
            "INSERT INTO events (ts, kind, correct, detail) VALUES (?,?,?,?)",
            (now, "pomodoro", 1, json.dumps({"minutes": minutes})),
        )
        self._conn.commit()

    def stats(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(correct),0) c, COALESCE(SUM(total),0) t"
            " FROM cards"
        ).fetchone()
        now = time.time()
        due = self._conn.execute("SELECT COUNT(*) FROM cards WHERE due_ts <= ?", (now,)).fetchone()[0]
        events = self._conn.execute(
            "SELECT ts, correct FROM events WHERE kind='answer' ORDER BY ts"
        ).fetchall()
        sessions = self._conn.execute(
            "SELECT kind, started_ts, duration_s, answered, correct FROM sessions ORDER BY started_ts"
        ).fetchall()
        return {
            "cards": row["n"],
            "total_answers": row["t"],
            "total_correct": row["c"],
            "accuracy": (row["c"] / row["t"] * 100.0) if row["t"] else 0.0,
            "due": due,
            "answer_events": [(e["ts"], e["correct"]) for e in events],
            "sessions": [{k: s[k] for k in s.keys()} for s in sessions],
        }

    def close(self) -> None:
        self._conn.close()
