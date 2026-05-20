import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from handlers import handle_message
from reminders import check_reminders

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Слушаем все сообщения (текст + медиа)
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        handle_message
    ))
    # Команды тоже обрабатываем через handle_message (там свой роутинг по топику)
    app.add_handler(MessageHandler(
        filters.COMMAND,
        handle_message
    ))

    # Проверка напоминаний каждый час
    app.job_queue.run_repeating(check_reminders, interval=3600, first=30)

    log.info("Бот запущен ✅")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
