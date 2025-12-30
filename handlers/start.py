# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes

from services.users import get_all_users
from services.bindings import get_binding_by_telegram_id
from ui import main_menu, build_users_pagination


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id

    # Уже привязан
    internal_id = get_binding_by_telegram_id(tg_id)
    if internal_id is not None:
        context.user_data["internal_id"] = internal_id
        await update.message.reply_text(
            "С возвращением! 👋",
            reply_markup=main_menu(),
        )
        return

    # Не привязан — показываем список с пагинацией
    users = get_all_users()

    await update.message.reply_text(
        "Выбери себя из списка:",
        reply_markup=build_users_pagination(
            users=users,
            page=0,
            action="select_self",
            show_back_to_menu=False,
        ),
    )
