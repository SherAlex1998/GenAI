from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class SteamDBManager:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database was not found: {self.db_path}")

    def execute_query(self, query: str, params: tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_games(self, search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = """
            SELECT appid, name, release_date, price
            FROM steam_games
            WHERE name LIKE ?
            ORDER BY positive_ratings DESC
            LIMIT ?
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, (f"%{search_text}%", limit))
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

