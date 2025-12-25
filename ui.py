# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from constants import REASONS

PAGE_SIZE = 10


def build_users_pagination(
    users: list[tuple[int, str]],
    page: int,
    action: str,
    show_back_to_menu: bool = False,
):
    """
    users: [(tg_id, name), ...]
    page: номер страницы (0-based)
    action: 'select_self' | 'choose_user'
    """

    total = len(users)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    page_users = users[start:end]

    keyboard = []

    # ===== Кнопки пользователей =====
    for user_id, name in page_users:
        keyboard.append(
            [InlineKeyboardButton(name, callback_data=f"{action}:user:{user_id}")]
        )

    # ===== Навигация =====
    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{action}:page:{page - 1}")
        )

    if end < total:
        nav.append(
            InlineKeyboardButton("➡️ Далее", callback_data=f"{action}:page:{page + 1}")
        )

    if nav:
        keyboard.append(nav)

    # ===== Возврат в меню =====
    if show_back_to_menu:
        keyboard.append(
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back")]
        )

    return InlineKeyboardMarkup(keyboard)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Поставить плюсик", callback_data="give_plus")],
        [InlineKeyboardButton("🛍️ Магазин", callback_data="shop")],
        [InlineKeyboardButton("� Мои покупки", callback_data="purchases")],
        [InlineKeyboardButton("�📊 Мой статус", callback_data="status")],
    ])


def reasons_keyboard():
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"reason:{key}")]
        for key, text in REASONS.items()
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)
