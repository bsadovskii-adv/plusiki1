# -*- coding: utf-8 -*-

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import DB_PATH
from constants import REASONS
from ui import main_menu, reasons_keyboard
from services.bindings import (
    get_binding_by_telegram_id,
    create_binding,
)
from services.pluses import save_plus
from services.users import get_user_name


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    tg_id = query.from_user.id

    # ========= BACK =========
    if data == "back":
        await query.message.reply_text("Главное меню:", reply_markup=main_menu())
        return

    # ========= SELECT SELF =========
    if data.startswith("select_self:"):
        user_id = int(data.split(":")[1])
        context.user_data["pending_self_id"] = user_id

        name = get_user_name(user_id)

        keyboard = [
            [InlineKeyboardButton("✅ Да, это я", callback_data="confirm_self")],
            [InlineKeyboardButton("❌ Нет, вернуться", callback_data="cancel_self")],
        ]

        await query.message.reply_text(
            f"Подтверди, что ты — {name}:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if data == "confirm_self":
        user_id = context.user_data.get("pending_self_id")
        if not user_id:
            await query.message.reply_text("Ошибка. Начни заново.")
            return

        success = create_binding(tg_id, user_id)
        if not success:
            await query.message.reply_text(
                "❌ Этот пользователь уже занят.",
                reply_markup=main_menu(),
            )
            context.user_data.clear()
            return

        context.user_data.clear()
        context.user_data["internal_id"] = user_id

        await query.message.reply_text(
            "✅ Ты успешно вошёл!",
            reply_markup=main_menu(),
        )
        return

    if data == "cancel_self":
        context.user_data.clear()
        await query.message.reply_text(
            "Выбор отменён. Используй /start",
        )
        return

    # ========= GIVE PLUS =========
    if data == "give_plus":
        internal_id = get_binding_by_telegram_id(tg_id)
        if not internal_id:
            await query.message.reply_text(
                "Сначала выбери себя через /start",
                reply_markup=main_menu(),
            )
            return

        context.user_data["internal_id"] = internal_id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT id, name FROM users WHERE id != ? ORDER BY name",
            (internal_id,),
        )
        users = c.fetchall()
        conn.close()

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"choose:{uid}")]
            for uid, name in users
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])

        await query.message.reply_text(
            "Кому поставить плюсик?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # ========= CHOOSE USER =========
    if data.startswith("choose:"):
        to_id = int(data.split(":")[1])
        context.user_data["plus_to"] = to_id

        await query.message.reply_text(
            "За что ставим плюсик?",
            reply_markup=reasons_keyboard(),
        )
        return

    # ========= REASON =========
    if data.startswith("reason:"):
        key = data.split(":", 1)[1]

        if key == "other":
            context.user_data["awaiting_custom_reason"] = True
            await query.message.reply_text("✍️ Напиши свою причину")
            return

        context.user_data["pending_reason"] = REASONS[key]

        keyboard = [
            [InlineKeyboardButton("✍️ Добавить комментарий", callback_data="add_comment")],
            [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_comment")],
        ]

        await query.message.reply_text(
            "Хочешь добавить комментарий?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # ========= SKIP COMMENT =========
    if data == "skip_comment":
        save_plus(
            from_id=context.user_data["internal_id"],
            to_id=context.user_data["plus_to"],
            reason=context.user_data["pending_reason"],
            comment=None,
        )
        context.user_data.clear()
        await query.message.reply_text(
            "✅ Плюсик добавлен!",
            reply_markup=main_menu(),
        )
        return

    # ========= ADD COMMENT =========
    if data == "add_comment":
        context.user_data["awaiting_comment_text"] = True
        await query.message.reply_text("✍️ Напиши комментарий (до 300 символов)")
        return

    # ========= STATUS =========
    if data == "status":
        internal_id = get_binding_by_telegram_id(tg_id)
        if not internal_id:
            await query.message.reply_text(
                "Сначала выбери себя через /start",
                reply_markup=main_menu(),
            )
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            SELECT p.reason, p.comment, u.name
            FROM pluses p
            JOIN users u ON u.id = p.from_id
            WHERE p.to_id = ?
            ORDER BY p.created_at DESC
            """,
            (internal_id,),
        )
        rows = c.fetchall()
        conn.close()

        if not rows:
            text = "У тебя пока нет плюсиков 🙂"
        else:
            lines = []
            for reason, comment, name in rows:
                line = f"• {reason} — от {name}"
                if comment:
                    line += f"\n   💬 {comment}"
                lines.append(line)
            text = f"🌟 Твои плюсики ({len(rows)}):\n" + "\n".join(lines)

        await query.message.reply_text(text, reply_markup=main_menu())
        return
