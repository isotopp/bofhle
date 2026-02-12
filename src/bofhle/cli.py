from __future__ import annotations

import argparse
import logging
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from bofhle.bofhle import (
    filter_candidates,
    histogram,
    load_words,
    play_game,
    score_wordle,
    suggest_coverage,
    suggest_entropy,
    suggest_shannon,
    suggest_top,
    validate_guess,
    validate_result,
)
from bofhle.database import DB_PATH, init_db, load_history, reset_db, store_guess


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bofhle helper")
    parser.add_argument("--guess", help="Your five-letter guess.")
    result_group = parser.add_mutually_exclusive_group()
    result_group.add_argument("--result", help="Result string using b/y/g (e.g. bbygg).")
    result_group.add_argument(
        "--secret",
        help="Secret word used to simulate a game result for --guess.",
    )
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
        default="most-likely",
        choices=["entropy", "shannon", "most-likely", "coverage"],
        help=(
            "Strategy: most-likely (default, fast), entropy (expected remaining), "
            "shannon (information gain), "
            "coverage (exploration only)."
        ),
    )
    candidate_group = parser.add_mutually_exclusive_group()
    candidate_group.add_argument(
        "--candidate",
        action="store_true",
        help=(
            "Use candidate-only guesses (default). With --test, "
            "switches to candidate-only after the first two guesses."
        ),
    )
    candidate_group.add_argument(
        "--words",
        dest="candidate",
        action="store_false",
        help="Use the full word list for guesses (opposite of --candidate).",
    )
    parser.set_defaults(candidate=True)
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

    if args.test and (args.guess or args.result or args.secret or args.show or args.reset):
        raise SystemExit("--test cannot be combined with other options.")

    if args.show and (args.guess or args.result or args.secret):
        raise SystemExit("--show cannot be combined with --guess/--result/--secret.")

    has_feedback = bool(args.result or args.secret)
    if (args.guess and not has_feedback) or (has_feedback and not args.guess):
        raise SystemExit("Use --guess with exactly one of --result or --secret.")

    if args.test:
        import time

        log_suffix = "-candidate" if args.candidate else ""
        log_path = Path(f"bofhle-{args.strategy}{log_suffix}.log")
        logger = _configure_test_logger(log_path)

        start_time = time.time()
        candidate_only_after = 2 if args.candidate else 0
        results = [
            play_game(
                secret,
                words,
                strategy=args.strategy,
                candidate_only=args.candidate,
                candidate_only_after=candidate_only_after,
            )
            for secret in words
        ]
        elapsed_time = time.time() - start_time

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
        average = sum(guess_counts) / len(guess_counts)
        stats = histogram(guess_counts)

        logger.info("")
        logger.info("Summary")
        logger.info("Strategy: %s", args.strategy)
        logger.info("Games: %d", len(results))
        logger.info("Best: %d guesses", best)
        logger.info("Worst: %d guesses", worst)
        logger.info("Average: %.2f guesses", average)
        logger.info("Total time: %.2f seconds", elapsed_time)
        logger.info("Time per game: %.2f ms", (elapsed_time / len(results)) * 1000)
        logger.info("Histogram (guesses -> games):")
        for guesses in sorted(stats):
            logger.info("  %d -> %d", guesses, stats[guesses])
        return

    if args.reset:
        reset_db(_database_path())
        print("New session started.")

    if args.guess and has_feedback:
        guess = validate_guess(args.guess, words)
        if args.secret:
            secret = validate_guess(args.secret, words)
            result = score_wordle(guess, secret)
        else:
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

    suggestions: Sequence[tuple[int | float, str]]
    if args.strategy == "entropy":
        guess_pool = candidates if args.candidate else words
        suggestions = suggest_entropy(guess_pool, candidates, limit=10)
        suggestion_label = "Next guesses (expected remaining):"
    elif args.strategy == "shannon":
        guess_pool = candidates if args.candidate else words
        suggestions = suggest_shannon(guess_pool, candidates, limit=10)
        suggestion_label = "Next guesses (shannon entropy):"
    elif args.strategy == "most-likely":
        guess_pool = candidates if args.candidate else words
        suggestions = suggest_top(guess_pool, limit=10)
        suggestion_label = "Next guesses:"
    else:
        guess_pool = candidates if args.candidate else words
        suggestions = suggest_coverage(guess_pool, candidates, limit=10)
        suggestion_label = "Next guesses (min remaining if bbbbb):"

    print("guess  result")
    for row in history_rows:
        print(f"{row.guess}  {_format_result(row.result, args.emoji)}")
    print(f"Candidates remaining: {len(candidates)}")
    print(suggestion_label)
    for score, word in suggestions:
        print(f"{score:>4} {word}")
