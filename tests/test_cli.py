import sys
from pathlib import Path

import bofhle.cli as cli


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
