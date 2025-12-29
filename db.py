# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Ensure existing installations get the new column when upgrading
    c.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in c.fetchall()]
    if "is_admin" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

    c.execute("""
        CREATE TABLE IF NOT EXISTS telegram_bindings (
            telegram_id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS pluses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS shop_items (
            item_key TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock_limit INTEGER
        )
    """)

    conn.commit()
    conn.close()
