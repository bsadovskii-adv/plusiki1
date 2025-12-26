# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from services.pluses import save_plus
from services.users import add_user, user_exists, is_admin
from services.auth import get_or_restore_internal_id
from ui import admin_menu


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    tg_id = update.effective_user.id

    # ===== Добавление нового пользователя (администратор) =====
    if context.user_data.get("awaiting_new_user_name"):
        if len(text) < 2:
            await update.message.reply_text("Имя должно быть хотя бы из 2 символов.")
            return

        if user_exists(text):
            await update.message.reply_text(f"❌ Пользователь '{text}' уже существует.")
            return

        user_id = add_user(text, is_admin_flag=False)
        context.user_data.pop("awaiting_new_user_name", None)
        
        internal_id = get_or_restore_internal_id(context, tg_id)
        menu = admin_menu() if internal_id and is_admin(internal_id) else None
        
        await update.message.reply_text(
            f"✅ Пользователь '{text}' добавлен (ID: {user_id}).",
            reply_markup=menu,
        )
        return

    # ===== Кастомная причина (Другое) =====
    if context.user_data.get("awaiting_custom_reason"):
        if len(text) < 3:
            await update.message.reply_text("Опиши причину чуть подробнее 🙂")
            return

        context.user_data.pop("awaiting_custom_reason", None)
        context.user_data["pending_reason"] = f"Другое: {text}"

        keyboard = [
            [{"text": "✍️ Добавить комментарий", "callback_data": "add_comment"}],
            [{"text": "⏭ Пропустить", "callback_data": "skip_comment"}],
        ]

        await update.message.reply_text(
            "Хочешь добавить комментарий?",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(**btn) for btn in row] for row in keyboard]
            ),
        )
        return

    # ===== Ввод комментария =====
    if context.user_data.get("awaiting_comment_text"):
        comment = text[:300]

        try:
            save_plus(
                from_id=context.user_data["internal_id"],
                to_id=context.user_data["plus_to"],
                reason=context.user_data["pending_reason"],
                comment=comment,
            )
        except KeyError:
            await update.message.reply_text(
                "Что-то пошло не так, начни заново 🙏"
            )
            context.user_data.clear()
            return

        context.user_data.clear()
        await update.message.reply_text(
            "✅ Плюсик с комментарием успешно добавлен!"
        )
        return
