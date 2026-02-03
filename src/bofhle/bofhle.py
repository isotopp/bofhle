from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

WORD_LIST_PATH = Path(__file__).resolve().parents[2] / "bofhle.txt"
VALID_RESULT_CHARS = {"b", "y", "g"}


@dataclass(frozen=True)
class GuessResult:
    guess: str
    result: str


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
