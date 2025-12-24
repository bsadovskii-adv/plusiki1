# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes
from services.bindings import delete_binding


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    delete_binding(tg_id)
    context.user_data.clear()
    await update.message.reply_text("Вы вышли. Используй /start для входа.")
