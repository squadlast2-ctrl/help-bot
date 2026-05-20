import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import GROUP_ID, TOPIC_HELP, TOPIC_RETURN, TOPIC_GENERAL
import database as db
import ai

log = logging.getLogger(__name__)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # ── Временный отладчик — помогает узнать chat_id и thread_id ──────────────
    # Раскомментируй, напиши в каждый топик, посмотри логи Railway, закомментируй обратно
    # log.info(f"DEBUG chat_id={msg.chat_id}  thread_id={msg.message_thread_id}  text={msg.text!r}")

    # Только сообщения из нашей группы
    if msg.chat_id != GROUP_ID:
        return

    user   = msg.from_user
    name   = user.full_name or user.username or "друг"
    thread = msg.message_thread_id
    text   = msg.text or msg.caption or ""
    photos = [msg.photo[-1].file_id] if msg.photo else []

    # Сохраняем пользователя
    db.save_user(user.id, name)

    # ── ТОПИК: ПОМОЩЬ ─────────────────────────────────────────────────────────
    if thread == TOPIC_HELP:
        if not text and not photos:
            return

        db.save_event(user.id, text or "📷 фото", photos)
        reply = await ai.живой_отклик(text or "поделился фотографией помощи")

        await msg.reply_text(
            f"✨ Записал!\n\n{reply}\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "_Напомню через 30, 60 и 90 дней — спросить что вернулось_",
            parse_mode="Markdown"
        )

    # ── ТОПИК: ВОЗВРАТЫ ───────────────────────────────────────────────────────
    elif thread == TOPIC_RETURN:
        if not text and not photos:
            return

        event_id = db.save_return(user.id, text or "📷 фото", photos)

        if event_id:
            await msg.reply_text(
                "🔄 Записал возврат!\n\n"
                "Круг замкнулся ✨\n"
                "_Напиши /mirror в Общении чтобы увидеть связь_",
                parse_mode="Markdown"
            )
        else:
            await msg.reply_text(
                "⚠️ Не нашёл активной помощи к которой привязать возврат.\n"
                "Сначала запиши что-то в топике *Помощь*!",
                parse_mode="Markdown"
            )

    # ── ТОПИК: ОБЩЕНИЕ (команды) ──────────────────────────────────────────────
    elif thread == TOPIC_GENERAL:
        await handle_command(msg, user.id, name, text)


async def handle_command(msg, telegram_id: int, name: str, text: str):
    """Обрабатывает команды в топике Общение."""

    if text in ("/start", "/help", "помощь"):
        await msg.reply_text(
            "👋 Привет! Я *Круг помощи* — дневник добрых дел.\n\n"
            "📌 *Как пользоваться:*\n"
            "• Топик *Помощь* — пиши/отправляй фото когда помог кому-то\n"
            "• Топик *Возвраты* — записывай что вернулось к тебе\n\n"
            "📌 *Команды здесь:*\n"
            "/stats — твоя статистика\n"
            "/story — история твоих добрых дел\n"
            "/mirror — связь между помощью и возвратами\n"
            "/pattern — паттерны твоих дел",
            parse_mode="Markdown"
        )

    elif text == "/stats":
        s = db.get_stats(telegram_id)
        await msg.reply_text(
            f"📊 *Статистика {name}*\n\n"
            f"🤝 Всего помощей: *{s['total_events']}*\n"
            f"🔄 Возвратов: *{s['total_returns']}*\n"
            f"⏳ Активных (ждут возврата): *{s['active_events']}*\n"
            f"✅ Завершённых: *{s['closed_events']}*",
            parse_mode="Markdown"
        )

    elif text == "/story":
        events = db.get_all_events(telegram_id)
        if not events:
            await msg.reply_text("Пока нет записей. Начни с топика *Помощь*! ✨",
                                 parse_mode="Markdown")
            return
        await msg.reply_text("📖 Составляю твою историю...")
        story = await ai.летописец(events)
        await msg.reply_text(f"📖 *Твоя история:*\n\n{story}", parse_mode="Markdown")

    elif text == "/mirror":
        events  = db.get_all_events(telegram_id)
        returns = db.get_all_returns(telegram_id)
        if not events or not returns:
            await msg.reply_text(
                "🪞 Для зеркала нужны и *помощь* и *возвраты*.\n"
                "Пока маловато данных!",
                parse_mode="Markdown"
            )
            return
        await msg.reply_text("🪞 Смотрю в зеркало...")
        reflection = await ai.зеркало(events, returns)
        await msg.reply_text(f"🪞 *Зеркало:*\n\n{reflection}", parse_mode="Markdown")

    elif text == "/pattern":
        events = db.get_all_events(telegram_id)
        if not events:
            await msg.reply_text("Нужно больше записей для анализа паттернов.",
                                 parse_mode="Markdown")
            return
        await msg.reply_text("🔍 Анализирую паттерны...")
        pattern = await ai.паттерн_аналитик(events)
        await msg.reply_text(f"🔍 *Паттерны:*\n\n{pattern}", parse_mode="Markdown")
