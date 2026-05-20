import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import save_help_entry

logger = logging.getLogger(__name__)
router = Router()


class HelpStates(StatesGroup):
    waiting_for_description = State()


def _media_info(message: Message) -> tuple[str | None, str | None]:
    if message.photo:
        return message.photo[-1].file_id, "photo"
    if message.video:
        return message.video.file_id, "video"
    if message.video_note:
        return message.video_note.file_id, "video_note"
    if message.voice:
        return message.voice.file_id, "voice"
    if message.document:
        return message.document.file_id, "document"
    return None, None


@router.message(Command("помог"))
async def cmd_pomog(message: Message, state: FSMContext):
    user = message.from_user
    text_after_cmd = message.text.replace("/помог", "").strip() if message.text else ""
    if text_after_cmd:
        await _save_and_confirm(message, user, text_after_cmd, None, None, state)
    else:
        await state.set_state(HelpStates.waiting_for_description)
        await message.reply(
            "📝 Расскажи кому и как ты помог сегодня.\n"
            "Можешь написать текст, прикрепить фото, видео или кружочек."
        )


@router.message(HelpStates.waiting_for_description)
async def receive_help_description(message: Message, state: FSMContext):
    user = message.from_user
    text = message.caption or message.text or ""
    media_id, media_type = _media_info(message)
    if not text and not media_id:
        await message.reply("Напиши что-нибудь или прикрепи медиа 🙏")
        return
    await _save_and_confirm(message, user, text, media_id, media_type, state)


async def _save_and_confirm(message, user, text, media_id, media_type, state):
    entry = await save_help_entry(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name,
        text=text,
        media_url=media_id,
        media_type=media_type,
    )
    await state.clear()
    media_emoji = {"photo": "📸", "video": "🎥", "video_note": "⭕", "voice": "🎙️", "document": "📎"}.get(media_type, "")
    await message.reply(
        f"✅ Записал! {media_emoji}\n"
        f"ID записи: <code>#{entry['id']}</code>\n\n"
        f"Когда что-то вернётся — используй /вернулось",
        parse_mode="HTML",
    )
    logger.info(f"Новая запись помощи #{entry['id']} от {user.full_name}")
