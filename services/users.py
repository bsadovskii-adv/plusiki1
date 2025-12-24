# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM users ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_name(user_id: int) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
