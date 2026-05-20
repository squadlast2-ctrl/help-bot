from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

HELP_TEXT = """
🤝 <b>Бот Помощь</b> — фиксируй добро и наблюдай как оно возвращается.

<b>Записать помощь:</b>
/помог — запись кому и как помог (текст + фото/видео/кружок)

<b>Записать возврат:</b>
/вернулось — что хорошего вернулось в жизнь

<b>Статистика:</b>
/стата — твои записи за 30 дней
/стата60 — за 60 дней
/стата90 — за 90 дней
/группа — статистика всей группы

<b>ИИ-истории:</b>
/история — вдохновляющая история месяца от ИИ
/история90 — история за 90 дней
/паттерны — ИИ анализирует паттерны группы

<i>Бот автоматически напомнит если группа молчит 2+ дня 💫</i>
"""


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "👋 Привет! Я помогаю фиксировать добрые дела и отслеживать как они возвращаются.\n\n"
        + HELP_TEXT,
        parse_mode="HTML"
    )


@router.message(Command("помощь"))
async def cmd_help(message: Message):
    await message.reply(HELP_TEXT, parse_mode="HTML")
