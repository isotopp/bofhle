from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from bofhle.bofhle import (
    filter_candidates,
    load_words,
    suggest_top,
    validate_guess,
    validate_result,
)
from bofhle.database import DB_PATH, init_db, load_history, reset_db, store_guess


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bofhle helper")
    parser.add_argument("--guess", required=True, help="Your five-letter guess.")
    parser.add_argument(
        "--result",
        required=True,
        help="Result string using b/y/g (e.g. bbygg).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset stored guesses before recording this result.",
    )
    return parser.parse_args()


def _database_path() -> Path:
    return DB_PATH


def main() -> None:
    args = _parse_args()
    words = load_words()

    guess = validate_guess(args.guess, words)
    result = validate_result(args.result)

    if args.reset:
        reset_db(_database_path())

    with sqlite3.connect(_database_path()) as connection:
        init_db(connection)
        store_guess(connection, guess, result)
        history_rows = load_history(connection)

    candidates = filter_candidates(words, history_rows)
    if not candidates:
        raise SystemExit("No candidates remain. Check your inputs or reset the database.")

    suggestions = suggest_top(candidates, limit=10)

    print(f"Candidates remaining: {len(candidates)}")
    print("Next guesses:")
    for score, word in suggestions:
        print(f"{score:>4} {word}")
