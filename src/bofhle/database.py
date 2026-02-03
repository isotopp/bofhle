from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from bofhle.bofhle import GuessResult

DB_PATH = Path.home() / ".bofhle.db"


def init_db(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS guesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guess TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


def store_guess(connection: sqlite3.Connection, guess: str, result: str) -> None:
    created_at = datetime.now(UTC).isoformat()
    connection.execute(
        "INSERT INTO guesses (guess, result, created_at) VALUES (?, ?, ?)",
        (guess, result, created_at),
    )
    connection.commit()


def load_history(connection: sqlite3.Connection) -> list[GuessResult]:
    rows = connection.execute("SELECT guess, result FROM guesses ORDER BY id").fetchall()
    return [GuessResult(guess=row[0], result=row[1]) for row in rows]


def reset_db(path: Path = DB_PATH) -> None:
    if path.exists():
        path.unlink()
