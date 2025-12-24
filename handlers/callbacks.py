# -*- coding: utf-8 -*-

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import ContextTypes

from config import DB_PATH
from constants import REASONS
from ui import main_menu, reasons_keyboard, build_users_pagination
from services.bindings import (
    get_binding_by_telegram_id,
    create_binding,
)
from services.pluses import save_plus
from services.users import get_user_name, get_all_users


entities = []
current_offset = 0


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    tg_id = query.from_user.id

    # ========= BACK =========
    if data == "back":
        await query.message.reply_text("Главное меню:", reply_markup=main_menu())
        return

    # ========= SELECT SELF (with pagination support) =========
    if data.startswith("select_self:"):
        parts = data.split(":")

        # pagination: select_self:page:N
        if len(parts) >= 3 and parts[1] == "page":
            try:
                page = int(parts[2])
            except ValueError:
                await query.message.reply_text("Неверный номер страницы.")
                return
            users = get_all_users()
            await query.message.edit_reply_markup(
                reply_markup=build_users_pagination(
                    users=users, page=page, action="select_self", show_back_to_menu=False
                )
            )
            return

        # new format: select_self:user:ID
        if len(parts) >= 3 and parts[1] == "user":
            try:
                user_id = int(parts[2])
            except ValueError:
                await query.message.reply_text("Неверный пользователь.")
                return
        else:
            # legacy format: select_self:ID
            try:
                user_id = int(parts[1])
            except (IndexError, ValueError):
                await query.message.reply_text("Неверный пользователь.")
                return

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

        users = get_all_users()
        # exclude self
        users = [(uid, name) for uid, name in users if uid != internal_id]

        await query.message.reply_text(
            "Кому поставить плюсик  ?",
            entity=[
                MessageEntity(
                    type=MessageEntity.CUSTOM_EMOJI,
                    offset=22,
                    length=1,
                    custom_emoji_id="5458840666563970188" 
                )
            ],
            reply_markup=build_users_pagination(
                users=users, page=0, action="choose_user", show_back_to_menu=True
            ),
            
        )
        return

    # ========= CHOOSE USER (with pagination support) =========
    # new format: choose_user:page:N or choose_user:user:ID
    if data.startswith("choose_user:") or data.startswith("choose:"):
        # normalize legacy "choose:ID" to choose_user:user:ID
        if data.startswith("choose:") and not data.startswith("choose_user:"):
            parts = data.split(":")
            if len(parts) >= 2:
                try:
                    to_id = int(parts[1])
                    context.user_data["plus_to"] = to_id
                    await query.message.reply_text(
                        "За что ставим плюсик  ?",
                        entity=[
                            MessageEntity(
                                type=MessageEntity.CUSTOM_EMOJI,
                                offset=21,
                                length=1,
                                custom_emoji_id="5458840666563970188" 
                            )
                        ],
                        reply_markup=reasons_keyboard(),
                    )
                    return
                except ValueError:
                    await query.message.reply_text("Неверный пользователь.")
                    return

        parts = data.split(":")
        # pagination nav: choose_user:page:N
        if len(parts) >= 3 and parts[1] == "page":
            try:
                page = int(parts[2])
            except ValueError:
                await query.message.reply_text("Неверный номер страницы.")
                return
            internal_id = context.user_data.get("internal_id")
            users = get_all_users()
            if internal_id:
                users = [(uid, name) for uid, name in users if uid != internal_id]
            await query.message.edit_reply_markup(
                reply_markup=build_users_pagination(
                    users=users, page=page, action="choose_user", show_back_to_menu=True
                )
            )
            return

        # choose_user:user:ID
        if len(parts) >= 3 and parts[1] == "user":
            try:
                to_id = int(parts[2])
            except ValueError:
                await query.message.reply_text("Неверный пользователь.")
                return
            context.user_data["plus_to"] = to_id
            await query.message.reply_text(
                "За что ставим плюсик  ?",
                        entity=[
                            MessageEntity(
                                type=MessageEntity.CUSTOM_EMOJI,
                                offset=21,
                                length=1,
                                custom_emoji_id="5458840666563970188" 
                            )
                        ],
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
            "✅ Плюсик  добавлен!",
                        entity=[
                            MessageEntity(
                                type=MessageEntity.CUSTOM_EMOJI,
                                offset=10,
                                length=1,
                                custom_emoji_id="5458840666563970188" 
                            )
                        ],
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
            entities = []

            emoji_id = "5458840666563970188" 
            current_offset = 0

            header = f"🌟 Твои плюсики ({len(rows)}):\n"
            lines.append(header)
            current_offset += len(header)

            for reason, comment, name in rows:
                line = f"⬤ {reason} — от {name}"
                
                entities.append(
                    MessageEntity(
                        type=MessageEntity.CUSTOM_EMOJI,
                        offset=current_offset,  
                        length=1,
                        custom_emoji_id=emoji_id,
                    )
                )

                lines.append(line)
                current_offset += len(line)

                if comment:
                    comment_line = f"\n   💬 {comment}"
                    lines.append(comment_line)
                    current_offset += len(comment_line)

                lines.append("\n")
                current_offset += 1

            text = "".join(lines)


        await query.message.reply_text(text, entities=entities, reply_markup=main_menu())
        return