from bofhle.bofhle import score_wordle


def test_score_all_green() -> None:
    assert score_wordle("paste", "paste") == "ggggg"


def test_score_handles_duplicates() -> None:
    assert score_wordle("allay", "alarm") == "ggbyb"
