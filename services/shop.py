# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH

# Catalog: key -> (display name, price in pluses)
CATALOG = {
    "stickerpack": ("Новогодний стикерпак", 3),
    "big_sticker": ("Объёмный новогодний стикер", 1),
    "mug": ("Новогодняя термокружка", 10),
    "pots": ("Набор горшков для зеленых друзей", 8),
}


def get_catalog() -> dict:
    return CATALOG.copy()


def get_balance(user_id: int) -> int:
    """Calculate user's balance: received pluses minus spent pluses."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM pluses WHERE to_id = ?", (user_id,))
    received = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(price),0) FROM purchases WHERE user_id = ?", (user_id,))
    spent = c.fetchone()[0] or 0
    conn.close()
    return received - spent


def buy_item(user_id: int, item_key: str) -> tuple[bool, str]:
    """Attempt to buy an item. Returns (success, message)."""
    if item_key not in CATALOG:
        return False, "Товар не найден."

    name, price = CATALOG[item_key]
    balance = get_balance(user_id)
    if balance < price:
        return False, f"Недостаточно плюсов — нужно {price}, у тебя {balance}."

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO purchases (user_id, item_key, item_name, price) VALUES (?, ?, ?, ?)",
        (user_id, item_key, name, price),
    )
    conn.commit()
    conn.close()
    return True, f"Куплено: {name} за {price} плюсов. Остаток: {balance - price}."
