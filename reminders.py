import logging
from telegram.ext import ContextTypes
from config import GROUP_ID, TOPIC_GENERAL
import database as db
import ai

log = logging.getLogger(__name__)

DAYS_MAP = {"day_30": 30, "day_60": 60, "day_90": 90}


async def check_reminders(ctx: ContextTypes.DEFAULT_TYPE):
    """Запускается каждый час. Отправляет напоминания о возвратах."""
    log.info("Проверяю напоминания...")

    # ── 30 / 60 / 90 дней ─────────────────────────────────────────────────────
    for rem in db.get_pending_reminders():
        try:
            user  = rem.get("users", {})
            event = rem.get("events", {})
            name  = user.get("name", "друг")
            days  = DAYS_MAP.get(rem["type"], 30)
            desc  = event.get("description", "")

            text = await ai.напоминание(name, desc, days)

            mention = f"@{user.get('username', '')}" if user.get("username") else name

            await ctx.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=TOPIC_GENERAL,
                text=f"{mention}, {text}",
                parse_mode="Markdown"
            )
            db.mark_reminder_sent(rem["id"])
            log.info(f"Отправил {rem['type']} для user {user.get('telegram_id')}")

        except Exception as e:
            log.error(f"Ошибка при отправке напоминания {rem['id']}: {e}")

    # ── Тишина 2 дня ──────────────────────────────────────────────────────────
    for event in db.get_pending_silence_reminders():
        try:
            user = event.get("users", {})
            name = user.get("name", "друг")
            text = await ai.напоминание_тишина(name)

            mention = f"@{user.get('username', '')}" if user.get("username") else name

            await ctx.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=TOPIC_GENERAL,
                text=f"{mention}, {text}",
                parse_mode="Markdown"
            )
            log.info(f"Отправил silence_2d для user {user.get('telegram_id')}")

        except Exception as e:
            log.error(f"Ошибка при silence напоминании: {e}")
