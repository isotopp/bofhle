from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path

from bofhle.bofhle import (
    filter_candidates,
    histogram,
    load_words,
    play_game,
    suggest_coverage,
    suggest_entropy,
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
    parser.add_argument(
        "--strategy",
        default="entropy",
        choices=["entropy", "most-likely", "coverage"],
        help="Strategy for selecting the next guess.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Brute-force test: solve all games and log results.",
    )
    return parser.parse_args()


def _database_path() -> Path:
    return DB_PATH


def _format_result(result: str, use_emoji: bool) -> str:
    if not use_emoji:
        return result
    mapping = {"b": "⬛", "y": "🟨", "g": "🟩"}
    return "".join(mapping[ch] for ch in result)


def _configure_test_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("bofhle.test")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(message)s")
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def main() -> None:
    args = _parse_args()
    words = load_words()

    if args.test and (args.guess or args.result or args.show or args.reset):
        raise SystemExit("--test cannot be combined with other options.")

    if args.show and (args.guess or args.result):
        raise SystemExit("--show cannot be combined with --guess/--result.")

    if (args.guess and not args.result) or (args.result and not args.guess):
        raise SystemExit("Both --guess and --result are required together.")

    if args.test:
        logger = _configure_test_logger(Path("bofhle.log"))
        results = [play_game(secret, words) for secret in words]

        for game_result in results:
            logger.info(
                "secret=%s guesses=%d path=%s",
                game_result.secret,
                len(game_result.guesses),
                " ".join(game_result.guesses),
            )

        guess_counts = [len(game_result.guesses) for game_result in results]
        best = min(guess_counts)
        worst = max(guess_counts)
        stats = histogram(guess_counts)

        logger.info("")
        logger.info("Summary")
        logger.info("Games: %d", len(results))
        logger.info("Best: %d guesses", best)
        logger.info("Worst: %d guesses", worst)
        logger.info("Histogram (guesses -> games):")
        for guesses in sorted(stats):
            logger.info("  %d -> %d", guesses, stats[guesses])
        return

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

    if args.strategy == "entropy":
        suggestions = suggest_entropy(words, candidates, limit=10)
        suggestion_label = "Next guesses (expected remaining):"
    elif args.strategy == "most-likely":
        suggestions = suggest_top(candidates, limit=10)
        suggestion_label = "Next guesses:"
    else:
        suggestions = suggest_coverage(words, candidates, limit=10)
        suggestion_label = "Next guesses (min remaining if bbbbb):"

    print("guess  result")
    for row in history_rows:
        print(f"{row.guess}  {_format_result(row.result, args.emoji)}")
    print(f"Candidates remaining: {len(candidates)}")
    print(suggestion_label)
    for score, word in suggestions:
        print(f"{score:>4} {word}")
