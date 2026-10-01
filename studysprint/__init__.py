"""StudySprint — exam-cram companion: turn notes into quizzes."""
from . import checker, charts, extract, ingest, pomodoro, questions, quiz, scheduler

__all__ = ["checker", "charts", "extract", "ingest", "pomodoro",
           "questions", "quiz", "scheduler"]
__version__ = "1.0.0"
