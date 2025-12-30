# -*- coding: utf-8 -*-

import sqlite3
from config import DB_PATH

# Default seed catalog used on first run (key -> (name, price, stock_limit))
DEFAULT_CATALOG = {
    "stickerpack": ("Новогодний стикерпак", 3, None),
    "big_sticker": ("Объёмный новогодний стикер", 1, None),
    "mug": ("Новогодняя термокружка", 10, 25),
    "pots": ("Набор горшков для зеленых друзей", 8, None),
}


def _ensure_seeded():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM shop_items")
    count = c.fetchone()[0] or 0
    if count == 0:
        for key, (name, price, limit) in DEFAULT_CATALOG.items():
            c.execute(
                "INSERT OR IGNORE INTO shop_items (item_key, item_name, price, stock_limit) VALUES (?, ?, ?, ?)",
                (key, name, price, limit),
            )
        conn.commit()
    conn.close()


def get_catalog() -> dict:
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT item_key, item_name, price, stock_limit FROM shop_items")
    rows = c.fetchall()
    conn.close()
    return {row[0]: (row[1], row[2], row[3]) for row in rows}


def get_remaining_stock(item_key: str) -> int | None:
    """Get remaining stock for an item. Returns None if unlimited."""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT stock_limit FROM shop_items WHERE item_key = ?", (item_key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    limit = row[0]
    if limit is None:
        conn.close()
        return None
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
    _ensure_seeded()
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
    catalog = get_catalog()
    if item_key not in catalog:
        return False, "Товар не найден."

    name, price, _ = catalog[item_key]

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
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT item_name, price, created_at FROM purchases WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_items() -> list[tuple[str, str, int, int | None]]:
    """Get all shop items. Returns list of (item_key, item_name, price, stock_limit)."""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT item_key, item_name, price, stock_limit FROM shop_items ORDER BY item_name")
    rows = c.fetchall()
    conn.close()
    return rows


def get_recent_purchases(limit: int = 100) -> list[tuple[int, str, str, int, str]]:
    """Return list of recent purchases: (user_id, user_name, item_name, price, created_at)"""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT p.user_id, u.name, p.item_name, p.price, p.created_at FROM purchases p JOIN users u ON u.id = p.user_id ORDER BY p.created_at LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def add_item(item_key: str, item_name: str, price: int, stock_limit: int | None) -> tuple[bool, str]:
    """Add or update a shop item. Returns (success, message)."""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO shop_items (item_key, item_name, price, stock_limit) VALUES (?, ?, ?, ?) ON CONFLICT(item_key) DO UPDATE SET item_name=excluded.item_name, price=excluded.price, stock_limit=excluded.stock_limit",
            (item_key, item_name, price, stock_limit),
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return False, f"Ошибка при добавлении товара: {e}"
    conn.close()
    return True, f"Товар '{item_name}' ({item_key}) добавлен или обновлён."


def remove_item(item_key: str) -> tuple[bool, str]:
    """Remove a shop item by key. Returns (success, message)."""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT item_name FROM shop_items WHERE item_key = ?", (item_key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Товар не найден."
    item_name = row[0]
    try:
        c.execute("DELETE FROM shop_items WHERE item_key = ?", (item_key,))
        conn.commit()
    except Exception as e:
        conn.close()
        return False, f"Ошибка при удалении товара: {e}"
    conn.close()
    return True, f"Товар '{item_name}' ({item_key}) удалён."
