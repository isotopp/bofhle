from bofhle.bofhle import (filter_candidates, GuessResult, histogram, play_game, suggest_coverage,
                           suggest_top)


def test_filter_candidates_matches_wordle_score() -> None:
    words = ["quota", "paste", "bdiff"]
    history = [GuessResult(guess="paste", result="bybgb")]
    filtered = filter_candidates(words, history)
    assert "quota" in filtered
    assert "paste" not in filtered


def test_suggest_top_and_coverage_return_sorted() -> None:
    words = ["quota", "paste", "bdiff"]
    top = suggest_top(words, limit=2)
    coverage = suggest_coverage(words, words, limit=2)
    assert len(top) == 2
    assert len(coverage) == 2
    assert top[0][0] >= top[1][0]
    assert coverage[0][0] <= coverage[1][0]


def test_play_game_solves() -> None:
    words = ["quota", "paste", "bdiff"]
    result = play_game("quota", words)
    assert result.secret == "quota"
    assert result.guesses[-1] == "quota"


def test_histogram_counts() -> None:
    counts = histogram([1, 2, 2, 3])
    assert counts == {1: 1, 2: 2, 3: 1}
