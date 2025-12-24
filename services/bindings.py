# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH


def get_binding_by_telegram_id(tg_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT user_id FROM telegram_bindings WHERE telegram_id = ?",
        (tg_id,),
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def create_binding(telegram_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO telegram_bindings (telegram_id, user_id) VALUES (?, ?)",
            (telegram_id, user_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_binding(telegram_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "DELETE FROM telegram_bindings WHERE telegram_id = ?",
        (telegram_id,),
    )
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
