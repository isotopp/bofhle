import sys
from pathlib import Path

from rich.text import Text

import bofhle.cli as cli
from bofhle.database import init_db, load_history


def test_format_result_with_color() -> None:
    styled = cli._format_result("bybgb", "crane", True, "light")
    assert isinstance(styled, Text)
    assert styled.plain == " c  r  a  n  e "
    assert cli._format_result("bybgb", "crane", False, "light") == "bybgb"


def test_parse_args_theme_defaults_and_override(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["bofhle"])
    args = cli._parse_args()
    assert args.theme == "light"

    monkeypatch.setattr(sys, "argv", ["bofhle", "--theme", "dracula"])
    args = cli._parse_args()
    assert args.theme == "dracula"


def test_light_and_dark_themes_are_distinct() -> None:
    assert cli.THEMES["light"] != cli.THEMES["dark"]


def test_show_mode_prints_state(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "DB_PATH", tmp_path / "bofhle.db")
    monkeypatch.setattr(sys, "argv", ["bofhle", "--show", "--no-color"])

    cli.main()
    output = capsys.readouterr().out

    assert "Candidates remaining:" in output
    assert "Next guesses" in output


def test_show_mode_color_uses_merged_header(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "DB_PATH", tmp_path / "bofhle.db")
    monkeypatch.setattr(sys, "argv", ["bofhle", "--show"])

    cli.main()
    output = capsys.readouterr().out

    assert "guess/result" in output
    assert "guess  result" not in output


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
