import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from config import settings
from database import get_last_activity_date, get_group_stats
from ai_client import generate_reminder, generate_story

logger = logging.getLogger(__name__)


async def check_and_remind(bot: Bot):
    """Проверяет тишину в группе и шлёт напоминание."""
    last = await get_last_activity_date()
    if last is None:
        return

    # Убираем timezone-awareness если нужно
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    silence_days = (datetime.now(timezone.utc) - last).days
    if silence_days >= settings.REMINDER_SILENCE_DAYS:
        logger.info(f"Тишина {silence_days} дней — шлём напоминание")
        reminder = await generate_reminder()
        await bot.send_message(
            settings.GROUP_CHAT_ID,
            f"💬 {reminder}",
        )


async def send_monthly_story(bot: Bot):
    """Каждый месяц ИИ автоматически пишет историю в группу."""
    data = await get_group_stats(days=30)
    if not data["helps"] and not data["returns"]:
        return
    story = await generate_story(data["helps"], data["returns"], period_days=30)
    await bot.send_message(
        settings.GROUP_CHAT_ID,
        f"📖 <b>История месяца — автоматический итог</b>\n\n{story}",
        parse_mode="HTML",
    )
    logger.info("Отправлена автоматическая история месяца")


async def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # Каждый день в 10:00 — проверка тишины
    scheduler.add_job(
        check_and_remind,
        CronTrigger(hour=10, minute=0),
        args=[bot],
        id="daily_reminder",
        replace_existing=True,
    )

    # 1-го числа каждого месяца в 12:00 — история месяца
    scheduler.add_job(
        send_monthly_story,
        CronTrigger(day=1, hour=12, minute=0),
        args=[bot],
        id="monthly_story",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Планировщик запущен ✅")
