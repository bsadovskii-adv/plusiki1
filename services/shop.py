# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH

# Catalog: key -> (display name, price in pluses, stock limit or None for unlimited)
CATALOG = {
    "stickerpack": ("Новогодний стикерпак", 3, None),
    "big_sticker": ("Объёмный новогодний стикер", 1, None),
    "mug": ("Новогодняя термокружка", 10, 25),
    "pots": ("Набор горшков для зеленых друзей", 8, None),
}


def get_catalog() -> dict:
    return CATALOG.copy()


def get_remaining_stock(item_key: str) -> int | None:
    """Get remaining stock for an item. Returns None if unlimited."""
    if item_key not in CATALOG:
        return None
    _, _, limit = CATALOG[item_key]
    if limit is None:
        return None
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM purchases WHERE item_key = ?", (item_key,))
    sold = c.fetchone()[0] or 0
    conn.close()
    return max(0, limit - sold)


def is_in_stock(item_key: str) -> bool:
    """Check if item is available (not sold out)."""
    remaining = get_remaining_stock(item_key)
    if remaining is None:
        return True
    return remaining > 0


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

    name, price, limit = CATALOG[item_key]
    
    # Check stock
    if not is_in_stock(item_key):
        return False, f"{name} — закончился товар."
    
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


def get_user_purchases(user_id: int) -> list[tuple[str, int, str]]:
    """Get all purchases for a user. Returns list of (item_name, price, created_at)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT item_name, price, created_at FROM purchases WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows
