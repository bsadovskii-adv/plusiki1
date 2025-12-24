# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.users import get_all_users
from services.bindings import get_binding_by_telegram_id
from ui import main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id

    internal_id = get_binding_by_telegram_id(tg_id)
    if internal_id:
        context.user_data["internal_id"] = internal_id
        await update.message.reply_text("С возвращением! 👋", reply_markup=main_menu())
        return

    users = get_all_users()
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"select_self:{uid}")]
        for uid, name in users
    ]

    await update.message.reply_text(
        "Выбери себя из списка:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
