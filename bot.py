import os
import io
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler,
)
from database import get_or_create_user, create_event, get_active_events, \
    create_return, upload_photo
from ai import get_live_response, get_narrator_story

# ── Состояния диалога ─────────────────────────────────────────────────────────
WAITING_HELP_TEXT   = 1
WAITING_HELP_PHOTO  = 2
CHOOSING_EVENT      = 3
WAITING_RETURN_TEXT = 4
WAITING_RETURN_PHOTO= 5


# ── /start ────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(telegram_id=user.id, name=user.first_name)
    await update.message.reply_text(
        f"Привет, {user.first_name} 👋\n\n"
        "Это твой личный дневник добрых дел.\n\n"
        "Помог кому-то сегодня? Запиши — и я напомню спросить тебя "
        "через 30, 60 и 90 дней: что вернулось?\n\n"
        "Команды:\n"
        "/help — записать помощь\n"
        "/return — записать что вернулось\n"
        "/stats — моя статистика"
    )


# ── Запись помощи ─────────────────────────────────────────────────────────────

async def cmd_help_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Расскажи — кому сегодня помог и как? Просто напиши как другу, можно коротко."
    )
    return WAITING_HELP_TEXT


async def received_help_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["help_description"] = update.message.text
    context.user_data["help_photos_bytes"] = []

    await update.message.reply_text(
        "Принято ✓\n\nЕсть фото? Отправь — или нажми «Пропустить».",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Пропустить →", callback_data="skip_photo")
        ]])
    )
    return WAITING_HELP_PHOTO


async def received_help_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()

    context.user_data.setdefault("help_photos_bytes", []).append(
        (bytes(file_bytes), f"{photo.file_unique_id}.jpg")
    )
    await update.message.reply_text(
        "Фото добавлено ✓  Ещё фото или «Готово»?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Готово →", callback_data="skip_photo")
        ]])
    )
    return WAITING_HELP_PHOTO


async def save_help_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    description = context.user_data.get("help_description", "")

    event = create_event(user_id=user_id, description=description)
    event_id = event["id"]

    photo_urls = []
    for file_bytes, filename in context.user_data.get("help_photos_bytes", []):
        url = upload_photo(user_id, event_id, file_bytes, filename)
        photo_urls.append(url)

    if photo_urls:
        from database import db
        db.table("events").update({"photo_urls": photo_urls}).eq("id", event_id).execute()

    await query.edit_message_text("Сохраняю... ✍️")

    try:
        ai_reply = await get_live_response(
            description=description,
            user_id=user_id,
            has_photo=bool(photo_urls),
        )
        await query.edit_message_text(f"Записано ✓\n\n{ai_reply}")
    except Exception:
        await query.edit_message_text("Записано ✓\n\nСпасибо, что помогаешь!")

    context.user_data.clear()
    return ConversationHandler.END


# ── Запись возврата ───────────────────────────────────────────────────────────

async def cmd_return_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active = get_active_events(user_id)

    if not active:
        await update.message.reply_text(
            "Пока нет открытых историй — сначала запиши помощь через /help"
        )
        return ConversationHandler.END

    buttons = []
    for ev in active[:8]:
        date = ev["created_at"][:10]
        short = ev["description"][:40] + ("…" if len(ev["description"]) > 40 else "")
        buttons.append([InlineKeyboardButton(
            f"{date}: {short}",
            callback_data=f"event_{ev['id']}"
        )])

    await update.message.reply_text(
        "К какой истории записать возврат?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CHOOSING_EVENT


async def event_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    event_id = query.data.replace("event_", "")
    context.user_data["return_event_id"] = event_id

    await query.edit_message_text(
        "Что вернулось? Расскажи — деньги, удача, встреча, настроение? "
        "Любая неожиданная хорошая штука считается."
    )
    return WAITING_RETURN_TEXT


async def received_return_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["return_description"] = update.message.text

    await update.message.reply_text(
        "Есть фото момента? Или нажми «Пропустить».",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Пропустить →", callback_data="skip_return_photo")
        ]])
    )
    return WAITING_RETURN_PHOTO


async def received_return_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = bytes(await file.download_as_bytearray())
    context.user_data["return_photo"] = (file_bytes, f"{photo.file_unique_id}.jpg")

    await update.message.reply_text(
        "Фото добавлено ✓",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Сохранить →", callback_data="skip_return_photo")
        ]])
    )
    return WAITING_RETURN_PHOTO


async def save_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    event_id = context.user_data["return_event_id"]
    description = context.user_data["return_description"]

    photo_urls = []
    if "return_photo" in context.user_data:
        file_bytes, filename = context.user_data["return_photo"]
        url = upload_photo(user_id, event_id, file_bytes, filename, is_return=True)
        photo_urls.append(url)

    create_return(event_id=event_id, description=description, photo_urls=photo_urls)

    await query.edit_message_text("Сохраняю и готовлю историю… ✍️")

    try:
        story = await get_narrator_story(event_id=event_id, user_id=user_id)
        await query.edit_message_text(f"История закрыта ✓\n\n{story}")
    except Exception:
        await query.edit_message_text("История закрыта ✓\n\nКруг замкнулся.")

    context.user_data.clear()
    return ConversationHandler.END


# ── /stats ────────────────────────────────────────────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import db
    user_id = update.effective_user.id

    total = db.table("events").select("id", count="exact").eq("user_id", user_id).execute()
    closed = db.table("events").select("id", count="exact") \
        .eq("user_id", user_id).eq("status", "closed").execute()

    total_n  = total.count or 0
    closed_n = closed.count or 0
    active_n = total_n - closed_n

    await update.message.reply_text(
        f"Твоя статистика:\n\n"
        f"Всего помощей: {total_n}\n"
        f"Завершённых историй: {closed_n}\n"
        f"Ждут возврата: {active_n}"
    )


# ── Отмена ────────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Отменено. Можешь начать заново.")
    return ConversationHandler.END


# ── Запуск ────────────────────────────────────────────────────────────────────

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    help_conv = ConversationHandler(
        entry_points=[CommandHandler("help", cmd_help_start)],
        states={
            WAITING_HELP_TEXT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, received_help_text)],
            WAITING_HELP_PHOTO: [
                MessageHandler(filters.PHOTO, received_help_photo),
                CallbackQueryHandler(save_help_event, pattern="^skip_photo$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    return_conv = ConversationHandler(
        entry_points=[CommandHandler("return", cmd_return_start)],
        states={
            CHOOSING_EVENT:      [CallbackQueryHandler(event_chosen, pattern="^event_")],
            WAITING_RETURN_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_return_text)],
            WAITING_RETURN_PHOTO:[
                MessageHandler(filters.PHOTO, received_return_photo),
                CallbackQueryHandler(save_return, pattern="^skip_return_photo$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(help_conv)
    app.add_handler(return_conv)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
