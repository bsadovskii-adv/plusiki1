# -*- coding: utf-8 -*-

import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= REQSONS =================
REASONS = {
    "integr": "За интеграцию новых коллег в МЛА+",
    "advice": "За профессиональный совет",
    "office": "За заботу об офисе",
    "events": "За организацию мероприятий",
    "lecture": "За проведение лекции",
    "support": "За эмоциональную поддержку",
    "content": "За контент в общем чате",
    "sport": "Развитие спорта в офисе",
    "pr": "PR и продвижение МЛА+",
    "other": "Другое",
}

# ================= CONFIG =================
DB_PATH = os.getenv("DB_PATH", "data.db")
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

# ================= DB =====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS pluses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    try:
        c.execute("ALTER TABLE pluses ADD COLUMN comment TEXT")
    except sqlite3.OperationalError:
        pass 

    conn.commit()
    conn.close()


# ================= UI =====================
def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Поставить плюсик", callback_data="give_plus")],
            [InlineKeyboardButton("📊 Мой статус", callback_data="status")],
        ]
    )

# ================= HELPERS =================
def get_user_name(tg_id: int) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE tg_id = ?", (tg_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ================= HANDLERS =================

def save_plus(from_id: int, to_id: int, reason: str, comment: str | None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO pluses (from_id, to_id, reason, comment)
        VALUES (?, ?, ?, ?)
        """,
        (from_id, to_id, reason, comment),
    )
    conn.commit()
    conn.close()




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    name = get_user_name(tg_id)

    if not name:
        await update.message.reply_text("👋 Привет! Как тебя зовут?")
        context.user_data.clear()
        context.user_data["awaiting_name"] = True
    else:
        await update.message.reply_text(
            f"С возвращением, {name}! 👋", reply_markup=main_menu()
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ===== Ввод имени =====
    if context.user_data.get("awaiting_name"):
        if len(text) < 2:
            await update.message.reply_text("Имя слишком короткое, попробуй ещё раз 🙂")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO users (tg_id, name) VALUES (?, ?)",
            (update.effective_user.id, text),
        )
        conn.commit()
        conn.close()

        context.user_data.clear()
        await update.message.reply_text(
            f"Рад знакомству, {text}! 🎉", reply_markup=main_menu()
        )
        return

    # ===== Ввод кастомной причины =====
    if context.user_data.get("awaiting_custom_reason"):
        if len(text) < 3:
            await update.message.reply_text("Опиши причину чуть подробнее 🙂")
            return

        to_id = context.user_data.get("plus_to")
        if not to_id:
            await update.message.reply_text(
                "Что-то пошло не так, попробуй ещё раз 🙏",
                reply_markup=main_menu(),
            )
            context.user_data.clear()
            return

        save_plus(
            from_id=update.effective_user.id,
            to_id=to_id,
            reason=f"Другое: {text}",
        )

        context.user_data.clear()
        await update.message.reply_text(
            "✅ Плюсик успешно добавлен!",
            reply_markup=main_menu(),
        )
        return
    
    if context.user_data.get("awaiting_comment_text"):
      comment = text[:300]

      save_plus(
          from_id=update.effective_user.id,
          to_id=context.user_data["plus_to"],
          reason=context.user_data["pending_reason"],
          comment=comment,
      )

      context.user_data.clear()
      await update.message.reply_text(
          "✅ Плюсик с комментарием успешно добавлен!",
          reply_markup=main_menu(),
      )
      return




async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ===== Поставить плюсик =====
    if data == "give_plus":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT tg_id, name FROM users WHERE tg_id != ?",
            (query.from_user.id,),
        )
        users = c.fetchall()
        conn.close()

        if not users:
            await query.message.reply_text("Пока некому ставить плюсики 🙂", reply_markup=main_menu())
            return

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"choose:{uid}")]
            for uid, name in users
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])

        await query.message.reply_text("Кому поставить плюсик?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ===== Выбор пользователя =====
    if data.startswith("choose:"):
        to_id = int(data.split(":")[1])

        if to_id == query.from_user.id:
            await query.message.reply_text("Нельзя поставить плюсик самому себе 😅", reply_markup=main_menu())
            return

        context.user_data.clear()
        context.user_data["plus_to"] = to_id

        keyboard = []
        for key, title in REASONS.items():
            keyboard.append(
                [InlineKeyboardButton(title, callback_data=f"reason:{key}")]
            )

        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])

        await query.message.reply_text("За что ставим плюсик?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ===== Причина =====
    if data.startswith("reason:"):
        key = data.split(":", 1)[1]

        if key == "other":
            context.user_data["awaiting_custom_reason"] = True
            await query.message.reply_text("✍️ Напиши свою причину")
            return

        # сохраняем причину, но НЕ пишем в БД
        reason_text = REASONS[key]
        context.user_data["pending_reason"] = reason_text
        context.user_data["awaiting_comment_choice"] = True

        keyboard = [
            [InlineKeyboardButton("✍️ Добавить комментарий", callback_data="add_comment")],
            [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_comment")],
        ]

        await query.message.reply_text(
            "Хочешь добавить комментарий к плюсику?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return



    # ===== Статус =====
    if data == "status":
        tg_id = query.from_user.id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            SELECT p.reason, p.comment, u.name
            FROM pluses p
            JOIN users u ON u.tg_id = p.from_id
            WHERE p.to_id = ?
            ORDER BY p.created_at DESC
            """,
            (tg_id,),
        )
        rows = c.fetchall()
        conn.close()
        
        lines = []
        if not rows:
            text = "У тебя пока нет плюсиков 🙂"
        else:
            for reason, comment, name in rows:
                line = f"• {reason} — от {name}"
                if comment:
                    line += f"\n   💬 {comment}"
                lines.append(line)

            text = f"🌟 Твои плюсики ({len(rows)}):\n" + "\n".join(lines)

        await query.message.reply_text(text, reply_markup=main_menu())
        return

    # ===== Назад =====
    if data == "back":
        await query.message.reply_text("Главное меню:", reply_markup=main_menu())
        return

    # ===== Пропуск причины =====
    if data == "skip_comment":
      save_plus(
          from_id=query.from_user.id,
          to_id=context.user_data["plus_to"],
          reason=context.user_data["pending_reason"],
          comment=None,
      )

      context.user_data.clear()
      await query.message.reply_text(
          "✅ Плюсик добавлен без комментария!",
          reply_markup=main_menu(),
      )
      return

    # ===== Добавлен комментарий =====    
    if data == "add_comment":
      context.user_data["awaiting_comment_text"] = True
      await query.message.reply_text("✍️ Напиши комментарий (до 300 символов)")
      return





# ================= MAIN ====================
def main():
    print("=== TG PLUS BOT STARTED ===")
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
