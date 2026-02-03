import sqlite3
from pathlib import Path

from bofhle.database import init_db, load_history, reset_db, store_guess


def test_store_and_load_history() -> None:
    with sqlite3.connect(":memory:") as connection:
        init_db(connection)
        store_guess(connection, "paste", "bybgb")
        store_guess(connection, "quota", "ggggg")
        history = load_history(connection)

    assert [entry.guess for entry in history] == ["paste", "quota"]
    assert [entry.result for entry in history] == ["bybgb", "ggggg"]


def test_reset_db_removes_file(tmp_path: Path) -> None:
    db_path = tmp_path / "bofhle.db"
    db_path.write_text("x")
    reset_db(db_path)
    assert not db_path.exists()
