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

def is_admin(user_id: int) -> bool:
    """Check if user is an administrator."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return bool(row and row[0])


def add_user(name: str, is_admin_flag: bool = False) -> int:
    """Add a new user and return their ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (name, is_admin) VALUES (?, ?)",
        (name, 1 if is_admin_flag else 0),
    )
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id


def user_exists(name: str) -> bool:
    """Check if a user with this name already exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    return bool(row)