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
