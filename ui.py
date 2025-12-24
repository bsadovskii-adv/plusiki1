# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from constants import REASONS


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Поставить плюсик", callback_data="give_plus")],
        [InlineKeyboardButton("📊 Мой статус", callback_data="status")],
    ])


def reasons_keyboard():
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"reason:{key}")]
        for key, text in REASONS.items()
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)
