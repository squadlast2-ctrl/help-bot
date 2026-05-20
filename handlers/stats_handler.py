import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import get_stats_for_user, get_group_stats
from ai_client import generate_story, analyze_patterns

logger = logging.getLogger(__name__)
router = Router()


def _format_stats_text(helps: list, returns: list, period: int, title: str) -> str:
    lines = [f"📊 <b>{title} — {period} дней</b>\n"]
    lines.append(f"🤝 Помощи: <b>{len(helps)}</b>")
    lines.append(f"🌟 Возвратов: <b>{len(returns)}</b>")
    if helps:
        lines.append("\n<b>Последние записи помощи:</b>")
        for h in helps[:5]:
            date = h["created_at"][:10]
            text = h["text"][:60] + "…" if len(h.get("text", "")) > 60 else h.get("text", "—")
            media = "📸" if h.get("media_type") == "photo" else ("🎥" if h.get("media_type") in ("video","video_note") else "")
            lines.append(f"  • {date} {media} {text}")
    if returns:
        lines.append("\n<b>Последние возвраты:</b>")
        for r in returns[:5]:
            date = r["created_at"][:10]
            text = r["text"][:60] + "…" if len(r.get("text", "")) > 60 else r.get("text", "—")
            lines.append(f"  ✨ {date} {text}")
    return "\n".join(lines)


@router.message(Command("стата"))
async def cmd_stats(message: Message):
    user = message.from_user
    data = await get_stats_for_user(user.id, days=30)
    text = _format_stats_text(data["helps"], data["returns"], 30, f"Статистика {user.first_name}")
    await message.reply(text, parse_mode="HTML")


@router.message(Command("стата60"))
async def cmd_stats60(message: Message):
    user = message.from_user
    data = await get_stats_for_user(user.id, days=60)
    text = _format_stats_text(data["helps"], data["returns"], 60, f"Статистика {user.first_name}")
    await message.reply(text, parse_mode="HTML")


@router.message(Command("стата90"))
async def cmd_stats90(message: Message):
    user = message.from_user
    data = await get_stats_for_user(user.id, days=90)
    text = _format_stats_text(data["helps"], data["returns"], 90, f"Статистика {user.first_name}")
    await message.reply(text, parse_mode="HTML")


@router.message(Command("группа"))
async def cmd_group_stats(message: Message):
    await message.reply("⏳ Собираю статистику группы...")
    data = await get_group_stats(days=30)
    text = _format_stats_text(data["helps"], data["returns"], 30, "Статистика группы")
    await message.reply(text, parse_mode="HTML")


@router.message(Command("история"))
async def cmd_story(message: Message):
    await message.reply("✨ Генерирую историю за 30 дней... (10-15 секунд)")
    data = await get_group_stats(days=30)
    if not data["helps"] and not data["returns"]:
        await message.reply("Пока нет записей для истории. Начните с /помог 🙏")
        return
    story = await generate_story(data["helps"], data["returns"], period_days=30)
    await message.reply(f"📖 <b>История месяца</b>\n\n{story}", parse_mode="HTML")


@router.message(Command("история90"))
async def cmd_story90(message: Message):
    await message.reply("✨ Генерирую историю за 90 дней...")
    data = await get_group_stats(days=90)
    if not data["helps"] and not data["returns"]:
        await message.reply("Пока нет записей для истории. Начните с /помог 🙏")
        return
    story = await generate_story(data["helps"], data["returns"], period_days=90)
    await message.reply(f"📖 <b>История 90 дней</b>\n\n{story}", parse_mode="HTML")


@router.message(Command("паттерны"))
async def cmd_patterns(message: Message):
    await message.reply("🔍 Анализирую паттерны...")
    data = await get_group_stats(days=90)
    if not data["helps"]:
        await message.reply("Нет данных для анализа. Начните с /помог 🙏")
        return
    analysis = await analyze_patterns(data["helps"], data["returns"])
    await message.reply(f"🧠 <b>Паттерны группы</b>\n\n{analysis}", parse_mode="HTML")
