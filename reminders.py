import os
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from database import db
from ai import get_silence_reminder, get_followup_reminder, get_pattern_insight, get_mirror_insight

load_dotenv()

# ── Детектор тишины (каждые 6 часов) ─────────────────────────────────────────

async def check_silence(bot: Bot):
    """Если пользователь не писал 2+ дня — отправляем живое напоминание."""
    try:
        users = db.table("users").select("telegram_id").execute()

        for user in users.data:
            user_id = user["telegram_id"]

            # Дата последней записи
            last = db.table("events") \
                .select("created_at") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            if not last.data:
                continue

            last_date = datetime.fromisoformat(last.data[0]["created_at"])
            if last_date.tzinfo is None:
                last_date = last_date.replace(tzinfo=timezone.utc)

            days_silent = (datetime.now(timezone.utc) - last_date).days

            if days_silent < 2:
                continue

            # Проверяем не слали ли уже сегодня
            from database import reminder_already_sent, mark_reminder_sent
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            reminder_type = f"silence_{today}"

            if reminder_already_sent(user_id, None, "silence_2d"):
                # Проверяем была ли запись после последнего напоминания
                last_reminder = db.table("reminders") \
                    .select("created_at") \
                    .eq("user_id", user_id) \
                    .eq("type", "silence_2d") \
                    .eq("sent", True) \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()

                if last_reminder.data:
                    reminder_date = datetime.fromisoformat(last_reminder.data[0]["created_at"])
                    if reminder_date.tzinfo is None:
                        reminder_date = reminder_date.replace(tzinfo=timezone.utc)
                    # Если с момента напоминания прошло меньше 2 дней — пропускаем
                    if (datetime.now(timezone.utc) - reminder_date).days < 2:
                        continue

            text = await get_silence_reminder()
            await bot.send_message(chat_id=user_id, text=text)
            mark_reminder_sent(user_id, None, "silence_2d")
            print(f"Silence reminder sent to {user_id}")

    except Exception as e:
        print(f"check_silence error: {e}")


# ── Контрольные напоминания 30/60/90 дней ────────────────────────────────────

async def check_followups(bot: Bot):
    """Проверяет все активные события и шлёт напоминания на 30/60/90 день."""
    try:
        events = db.table("events") \
            .select("id, user_id, description, created_at") \
            .eq("status", "active") \
            .execute()

        for event in events.data:
            event_id = event["id"]
            user_id = event["user_id"]
            description = event["description"]

            created_at = datetime.fromisoformat(event["created_at"])
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            days_passed = (datetime.now(timezone.utc) - created_at).days

            from database import reminder_already_sent, mark_reminder_sent

            for milestone in [30, 60, 90]:
                reminder_type = f"day_{milestone}"

                # Попадаем в окно ±1 день от milestone
                if abs(days_passed - milestone) > 1:
                    continue

                # Уже отправляли?
                if reminder_already_sent(user_id, event_id, reminder_type):
                    continue

                text = await get_followup_reminder(description, days_passed)
                await bot.send_message(chat_id=user_id, text=text)
                mark_reminder_sent(user_id, event_id, reminder_type)
                print(f"Followup {milestone}d reminder sent to {user_id} for event {event_id}")

    except Exception as e:
        print(f"check_followups error: {e}")


# ── Еженедельный паттерн-аналитик (каждый понедельник) ───────────────────────

async def send_weekly_pattern(bot: Bot):
    """Раз в неделю анализирует паттерны и отправляет инсайт."""
    try:
        users = db.table("users").select("telegram_id").execute()

        for user in users.data:
            user_id = user["telegram_id"]

            from database import reminder_already_sent, mark_reminder_sent
            if reminder_already_sent(user_id, None, "mirror"):
                continue

            insight = await get_pattern_insight(user_id)
            if not insight:
                continue

            await bot.send_message(
                chat_id=user_id,
                text=f"📊 Твои паттерны за неделю:\n\n{insight}"
            )
            mark_reminder_sent(user_id, None, "mirror")
            print(f"Weekly pattern sent to {user_id}")

    except Exception as e:
        print(f"send_weekly_pattern error: {e}")


# ── Месячное зеркало (1-го числа каждого месяца) ─────────────────────────────

async def send_monthly_mirror(bot: Bot):
    """Раз в месяц отправляет профиль помощника."""
    try:
        users = db.table("users").select("telegram_id").execute()

        for user in users.data:
            user_id = user["telegram_id"]

            mirror = await get_mirror_insight(user_id)
            if not mirror:
                continue

            await bot.send_message(
                chat_id=user_id,
                text=f"🪞 Твой месяц:\n\n{mirror}"
            )
            print(f"Monthly mirror sent to {user_id}")

    except Exception as e:
        print(f"send_monthly_mirror error: {e}")


# ── Запуск планировщика ───────────────────────────────────────────────────────

def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Создаёт и запускает планировщик.
    Вызывается из bot.py после запуска приложения.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Тишина — проверяем каждые 6 часов
    scheduler.add_job(
        check_silence,
        trigger="interval",
        hours=6,
        args=[bot],
        id="silence_check",
    )

    # Контрольные напоминания — каждый день в 10:00 UTC
    scheduler.add_job(
        check_followups,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot],
        id="followup_check",
    )

    # Еженедельный паттерн — каждый понедельник в 11:00 UTC
    scheduler.add_job(
        send_weekly_pattern,
        trigger="cron",
        day_of_week="mon",
        hour=11,
        minute=0,
        args=[bot],
        id="weekly_pattern",
    )

    # Месячное зеркало — 1-го числа в 12:00 UTC
    scheduler.add_job(
        send_monthly_mirror,
        trigger="cron",
        day=1,
        hour=12,
        minute=0,
        args=[bot],
        id="monthly_mirror",
    )

    scheduler.start()
    print("Scheduler started ✓")
    return scheduler
