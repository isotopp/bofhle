from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

WORD_LIST_PATH = Path(__file__).resolve().parents[2] / "bofhle.txt"
DB_PATH = Path.home() / ".bofhle.db"
VALID_RESULT_CHARS = {"b", "y", "g"}


@dataclass(frozen=True)
class GuessResult:
    guess: str
    result: str


def _load_words(path: Path) -> list[str]:
    words = [line.strip().lower() for line in path.read_text().splitlines()]
    return [word for word in words if len(word) == 5]


def _score_wordle(guess: str, candidate: str) -> str:
    result = ["b"] * 5
    candidate_remaining: dict[str, int] = {}

    for idx, (g_letter, c_letter) in enumerate(zip(guess, candidate, strict=True)):
        if g_letter == c_letter:
            result[idx] = "g"
        else:
            candidate_remaining[c_letter] = candidate_remaining.get(c_letter, 0) + 1

    for idx, g_letter in enumerate(guess):
        if result[idx] != "b":
            continue
        remaining = candidate_remaining.get(g_letter, 0)
        if remaining > 0:
            result[idx] = "y"
            candidate_remaining[g_letter] = remaining - 1

    return "".join(result)


def _filter_candidates(words: list[str], history: list[GuessResult]) -> list[str]:
    candidates = words
    for item in history:
        candidates = [word for word in candidates if _score_wordle(item.guess, word) == item.result]
    return candidates


def _most_likely(candidates: list[str]) -> str:
    if not candidates:
        raise ValueError("No candidates remain.")

    position_counts: list[dict[str, int]] = [dict() for _ in range(5)]
    for word in candidates:
        for idx, letter in enumerate(word):
            bucket = position_counts[idx]
            bucket[letter] = bucket.get(letter, 0) + 1

    def score(word: str) -> int:
        return sum(position_counts[idx].get(letter, 0) for idx, letter in enumerate(word))

    return max(candidates, key=score)


def _init_db(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS guesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guess TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


def _store_guess(connection: sqlite3.Connection, guess: str, result: str) -> None:
    created_at = datetime.now(UTC).isoformat()
    connection.execute(
        "INSERT INTO guesses (guess, result, created_at) VALUES (?, ?, ?)",
        (guess, result, created_at),
    )
    connection.commit()


def _load_history(connection: sqlite3.Connection) -> list[GuessResult]:
    rows = connection.execute("SELECT guess, result FROM guesses ORDER BY id").fetchall()
    return [GuessResult(guess=row[0], result=row[1]) for row in rows]


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
    parser.add_argument(
        "--strategy",
        default="most-likely",
        choices=["most-likely"],
        help="Strategy for selecting the next guess.",
    )
    return parser.parse_args()


def _validate_guess(guess: str, words: list[str]) -> str:
    normalized = guess.strip().lower()
    if len(normalized) != 5 or not normalized.isalpha():
        raise ValueError("Guess must be exactly five letters.")
    if normalized not in words:
        raise ValueError("Guess must be a valid bofhle command from bofhle.txt.")
    return normalized


def _validate_result(result: str) -> str:
    normalized = result.strip().lower()
    if len(normalized) != 5 or any(ch not in VALID_RESULT_CHARS for ch in normalized):
        raise ValueError("Result must be five characters of only b, y, or g.")
    return normalized


def main() -> None:
    args = _parse_args()
    words = _load_words(WORD_LIST_PATH)

    guess = _validate_guess(args.guess, words)
    result = _validate_result(args.result)

    if args.reset and DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as connection:
        _init_db(connection)
        _store_guess(connection, guess, result)
        history = _load_history(connection)

    candidates = _filter_candidates(words, history)
    if not candidates:
        raise SystemExit("No candidates remain. Check your inputs or reset the database.")

    if args.strategy == "most-likely":
        next_guess = _most_likely(candidates)
    else:
        raise SystemExit(f"Unknown strategy: {args.strategy}")

    print(f"Candidates remaining: {len(candidates)}")
    print(f"Next guess ({args.strategy}): {next_guess}")
