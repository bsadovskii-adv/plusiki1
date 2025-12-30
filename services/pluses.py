# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH


def save_plus(from_id: int, to_id: int, reason: str, comment: str | None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO pluses (from_id, to_id, reason, comment)
        VALUES (?, ?, ?, ?)
        """,
        (from_id, to_id, reason, comment),
    )
    conn.commit()
    conn.close()


def get_pluses_given_by_user(user_id: int) -> list[tuple[str, str, str]]:
    """Return pluses given by user: (reason, comment, recipient_name, created_at)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT p.reason, p.comment, u.name, p.created_at FROM pluses p JOIN users u ON u.id = p.to_id WHERE p.from_id = ? ORDER BY p.created_at DESC",
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_recent_pluses(limit: int = 100) -> list[tuple[int, str, int, str, str]]:
    """Return 100 most recent pluses ordered from oldest to newest (ASC).
    This fetches the newest 100 and displays them with oldest at top."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT p.from_id, fu.name, p.to_id, tu.name, p.reason, p.comment, p.created_at FROM pluses p JOIN users fu ON fu.id = p.from_id JOIN users tu ON tu.id = p.to_id ORDER BY p.created_at DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    # Reverse to show oldest first (from the 100 most recent)
    return list(reversed(rows))
