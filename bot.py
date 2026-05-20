import os
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from handlers import handle_message
from reminders import check_reminders

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = ApplicationBuilder().token(token).build()

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_message))

    app.job_queue.run_repeating(check_reminders, interval=3600, first=30)

    log.info("Бот запущен ✅")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
