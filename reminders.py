import os
import logging
from telegram.ext import ContextTypes
import database as db
import ai

log = logging.getLogger(__name__)

DAYS_MAP = {"day_30": 30, "day_60": 60, "day_90": 90}


async def check_reminders(ctx: ContextTypes.DEFAULT_TYPE):
    GROUP_ID      = int(os.environ.get("GROUP_ID", "0"))
    TOPIC_GENERAL = int(os.environ.get("TOPIC_GENERAL", "0"))

    log.info("Проверяю напоминания...")

    for rem in db.get_pending_reminders():
        try:
            user  = rem.get("users", {})
            event = rem.get("events", {})
            name  = user.get("name", "друг")
            days  = DAYS_MAP.get(rem["type"], 30)
            text  = await ai.напоминание(name, event.get("description", ""), days)
            mention = f"@{user['username']}" if user.get("username") else name
            await ctx.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=TOPIC_GENERAL,
                text=f"{mention}, {text}")
            db.mark_reminder_sent(rem["id"])
        except Exception as e:
            log.error(f"Ошибка напоминания: {e}")

    for event in db.get_pending_silence_reminders():
        try:
            user    = event.get("users", {})
            name    = user.get("name", "друг")
            text    = await ai.напоминание_тишина(name)
            mention = f"@{user['username']}" if user.get("username") else name
            await ctx.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=TOPIC_GENERAL,
                text=f"{mention}, {text}")
        except Exception as e:
            log.error(f"Ошибка silence: {e}")
