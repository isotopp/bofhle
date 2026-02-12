import sys
from pathlib import Path

import bofhle.cli as cli
from bofhle.database import init_db, load_history


def test_format_result_with_emoji() -> None:
    assert cli._format_result("bybgb", True) == "⬛🟨⬛🟩⬛"
    assert cli._format_result("bybgb", False) == "bybgb"


def test_show_mode_prints_state(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "DB_PATH", tmp_path / "bofhle.db")
    monkeypatch.setattr(sys, "argv", ["bofhle", "--show", "--no-emoji"])

    cli.main()
    output = capsys.readouterr().out

    assert "Candidates remaining:" in output
    assert "Next guesses" in output


def test_secret_computes_result_and_stores_it(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "DB_PATH", tmp_path / "bofhle.db")
    monkeypatch.setattr(sys, "argv", ["bofhle", "--guess", "paste", "--secret", "bdiff"])

    cli.main()

    with cli.sqlite3.connect(cli.DB_PATH) as connection:
        init_db(connection)
        history = load_history(connection)

    assert len(history) == 1
    assert history[0].guess == "paste"
    assert history[0].result == "bbbbb"


def test_secret_is_mutually_exclusive_with_result(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["bofhle", "--guess", "paste", "--result", "bbbbb", "--secret", "bdiff"],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected argparse to exit for mutually exclusive options.")
