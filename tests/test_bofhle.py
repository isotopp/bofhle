from bofhle.bofhle import (
    GuessResult,
    filter_candidates,
    histogram,
    play_game,
    select_guess_pool,
    suggest_coverage,
    suggest_entropy,
    suggest_shannon,
    suggest_top,
)


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
    entropy = suggest_entropy(words, words, limit=2)
    shannon = suggest_shannon(words, words, limit=2)
    assert len(top) == 2
    assert len(coverage) == 2
    assert len(entropy) == 2
    assert len(shannon) == 2
    assert top[0][0] >= top[1][0]
    assert coverage[0][0] <= coverage[1][0]
    assert entropy[0][0] <= entropy[1][0]
    assert shannon[0][0] >= shannon[1][0]


def test_play_game_solves() -> None:
    words = ["quota", "paste", "bdiff"]
    result = play_game("quota", words)
    assert result.secret == "quota"
    assert result.guesses[-1] == "quota"


def test_play_game_honors_strategy() -> None:
    words = ["quota", "paste", "bdiff"]
    for strategy in ["entropy", "shannon", "most-likely", "coverage"]:
        result = play_game("quota", words, strategy=strategy)
        assert result.secret == "quota"
        assert result.guesses[-1] == "quota"


def test_histogram_counts() -> None:
    counts = histogram([1, 2, 2, 3])
    assert counts == {1: 1, 2: 2, 3: 1}


def test_select_guess_pool_respects_candidate_mode() -> None:
    all_words = ["alpha", "bravo", "candy"]
    candidates = ["alpha", "candy"]
    assert (
        select_guess_pool(
            "entropy",
            all_words,
            candidates,
            candidate_only=False,
            guess_index=0,
            candidate_only_after=0,
        )
        == all_words
    )
    assert (
        select_guess_pool(
            "entropy",
            all_words,
            candidates,
            candidate_only=True,
            guess_index=0,
            candidate_only_after=1,
        )
        == all_words
    )
    assert (
        select_guess_pool(
            "entropy",
            all_words,
            candidates,
            candidate_only=True,
            guess_index=1,
            candidate_only_after=1,
        )
        == candidates
    )
    assert (
        select_guess_pool(
            "most-likely",
            all_words,
            candidates,
            candidate_only=False,
            guess_index=0,
            candidate_only_after=0,
        )
        == all_words
    )
