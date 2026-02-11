from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

WORD_LIST_PATH = Path(__file__).resolve().parents[2] / "bofhle.txt"
VALID_RESULT_CHARS = {"b", "y", "g"}


@dataclass(frozen=True)
class GuessResult:
    guess: str
    result: str


@dataclass(frozen=True)
class GameResult:
    secret: str
    guesses: list[str]


def load_words(path: Path = WORD_LIST_PATH) -> list[str]:
    words = [line.strip().lower() for line in path.read_text().splitlines()]
    return [word for word in words if len(word) == 5]


def score_wordle(guess: str, candidate: str) -> str:
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


def filter_candidates(words: list[str], history: list[GuessResult]) -> list[str]:
    candidates = words
    for item in history:
        candidates = [word for word in candidates if score_wordle(item.guess, word) == item.result]
    return candidates


def score_words(words: list[str]) -> list[tuple[int, str]]:
    letter_counts = Counter("".join(words))

    def score_word(word: str) -> int:
        return sum(letter_counts[ch] for ch in set(word))

    scored = [(score_word(word), word) for word in words]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def suggest_top(words: list[str], limit: int = 10) -> list[tuple[int, str]]:
    return score_words(words)[:limit]


def suggest_coverage(
    all_words: list[str],
    candidates: list[str],
    limit: int = 10,
) -> list[tuple[int, str]]:
    """Suggest words that maximize letter elimination.

    Scores words by how many candidates remain if the guess returns "bbbbb"
    (all letters wrong). Lower scores mean more candidates eliminated.

    This strategy is useful for exploration and narrowing possibilities, but
    is not designed to solve games (it actively avoids guessing the answer).
    Best used interactively or as part of a hybrid strategy.
    """
    scored: list[tuple[int, str]] = []
    for word in all_words:
        remaining = sum(1 for candidate in candidates if score_wordle(word, candidate) == "bbbbb")
        scored.append((remaining, word))
    scored.sort(key=lambda item: (item[0], item[1]))
    return scored[:limit]


def suggest_entropy(
    all_words: list[str],
    candidates: list[str],
    limit: int = 10,
) -> list[tuple[float, str]]:
    """Score words by expected information gain (lower is better)."""
    scored: list[tuple[float, str]] = []
    for guess in all_words:
        # Group candidates by result pattern
        pattern_groups: dict[str, list[str]] = {}
        for candidate in candidates:
            pattern = score_wordle(guess, candidate)
            pattern_groups.setdefault(pattern, []).append(candidate)

        # Calculate expected remaining candidates (lower is better)
        expected = sum(len(group) ** 2 for group in pattern_groups.values()) / len(candidates)
        scored.append((expected, guess))

    scored.sort(key=lambda item: (item[0], item[1]))
    return scored[:limit]


def suggest_shannon(
    all_words: list[str],
    candidates: list[str],
    limit: int = 10,
) -> list[tuple[float, str]]:
    """Score words by Shannon entropy (higher is better)."""
    scored: list[tuple[float, str]] = []
    total = len(candidates)
    for guess in all_words:
        pattern_counts: dict[str, int] = {}
        for candidate in candidates:
            pattern = score_wordle(guess, candidate)
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        entropy = 0.0
        for count in pattern_counts.values():
            probability = count / total
            entropy -= probability * math.log2(probability)

        scored.append((entropy, guess))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[:limit]


def select_guess_pool(
    strategy: str,
    all_words: list[str],
    candidates: list[str],
    candidate_only: bool,
    guess_index: int,
    candidate_only_after: int,
) -> list[str]:
    if strategy == "most-likely":
        return candidates
    if candidate_only and guess_index >= candidate_only_after:
        return candidates
    return all_words


def play_game(
    secret: str,
    words: list[str],
    strategy: str = "entropy",
    candidate_only: bool = False,
    candidate_only_after: int = 0,
) -> GameResult:
    history: list[GuessResult] = []
    candidates = words

    for guess_index in range(len(words) + 1):
        # If only one candidate remains, guess it directly
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            guess_pool = select_guess_pool(
                strategy,
                words,
                candidates,
                candidate_only,
                guess_index,
                candidate_only_after,
            )
            if strategy == "entropy":
                guess = suggest_entropy(guess_pool, candidates, limit=1)[0][1]
            elif strategy == "shannon":
                guess = suggest_shannon(guess_pool, candidates, limit=1)[0][1]
            elif strategy == "most-likely":
                guess = suggest_top(candidates, limit=1)[0][1]
            elif strategy == "coverage":
                guess = suggest_coverage(guess_pool, candidates, limit=1)[0][1]
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        result = score_wordle(guess, secret)
        history.append(GuessResult(guess=guess, result=result))
        if guess == secret:
            return GameResult(secret=secret, guesses=[entry.guess for entry in history])
        candidates = filter_candidates(words, history)

    raise RuntimeError(f"Failed to solve secret {secret}.")


def histogram(guess_counts: list[int]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for value in guess_counts:
        counts[value] = counts.get(value, 0) + 1
    return counts


def validate_guess(guess: str, words: list[str]) -> str:
    normalized = guess.strip().lower()
    if len(normalized) != 5 or not normalized.isalpha():
        raise ValueError("Guess must be exactly five letters.")
    if normalized not in words:
        raise ValueError("Guess must be a valid bofhle command from bofhle.txt.")
    return normalized


def validate_result(result: str) -> str:
    normalized = result.strip().lower()
    if len(normalized) != 5 or any(ch not in VALID_RESULT_CHARS for ch in normalized):
        raise ValueError("Result must be five characters of only b, y, or g.")
    return normalized
