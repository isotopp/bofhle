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
    parser.add_argument("--guess", help="Your five-letter guess.")
    parser.add_argument("--result", help="Result string using b/y/g (e.g. bbygg).")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset stored guesses before recording this result.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the current session state.",
    )
    parser.add_argument(
        "--emoji",
        dest="emoji",
        action="store_true",
        default=True,
        help="Display results using emoji squares (default).",
    )
    parser.add_argument(
        "--no-emoji",
        dest="emoji",
        action="store_false",
        help="Display results using letters b/y/g.",
    )
    return parser.parse_args()


def _database_path() -> Path:
    return DB_PATH


def _format_result(result: str, use_emoji: bool) -> str:
    if not use_emoji:
        return result
    mapping = {"b": "⬛", "y": "🟨", "g": "🟩"}
    return "".join(mapping[ch] for ch in result)


def main() -> None:
    args = _parse_args()
    words = load_words()

    if args.show and (args.guess or args.result):
        raise SystemExit("--show cannot be combined with --guess/--result.")

    if (args.guess and not args.result) or (args.result and not args.guess):
        raise SystemExit("Both --guess and --result are required together.")

    if args.reset:
        reset_db(_database_path())
        print("New session started.")

    if args.guess and args.result:
        guess = validate_guess(args.guess, words)
        result = validate_result(args.result)

        with sqlite3.connect(_database_path()) as connection:
            init_db(connection)
            store_guess(connection, guess, result)
            history_rows = load_history(connection)
    else:
        with sqlite3.connect(_database_path()) as connection:
            init_db(connection)
            history_rows = load_history(connection)

    candidates = filter_candidates(words, history_rows)
    if not candidates:
        raise SystemExit("No candidates remain. Check your inputs or reset the database.")

    suggestions = suggest_top(candidates, limit=10)

    print("guess  result")
    for row in history_rows:
        print(f"{row.guess}  {_format_result(row.result, args.emoji)}")
    print(f"Candidates remaining: {len(candidates)}")
    print("Next guesses:")
    for score, word in suggestions:
        print(f"{score:>4} {word}")
