import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from handlers import help_handler, stats_handler, return_handler, admin_handler
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(help_handler.router)
    dp.include_router(return_handler.router)
    dp.include_router(stats_handler.router)
    dp.include_router(admin_handler.router)

    await start_scheduler(bot)

    logger.info("Бот запущен ✅")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
