import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import save_return_entry, get_open_entries, get_entry_by_id

logger = logging.getLogger(__name__)
router = Router()


class ReturnStates(StatesGroup):
    choosing_entry = State()
    waiting_for_description = State()


@router.message(Command("вернулось"))
async def cmd_vernulosj(message: Message, state: FSMContext):
    user = message.from_user
    open_entries = await get_open_entries(user.id)
    if not open_entries:
        await message.reply(
            "У тебя нет открытых записей помощи.\n"
            "Сначала запиши помощь командой /помог 🙏"
        )
        return
    buttons = []
    for e in open_entries[:8]:
        label = e["text"][:40] + "…" if len(e.get("text", "")) > 40 else e.get("text", "—")
        date = e["created_at"][:10]
        buttons.append([InlineKeyboardButton(
            text=f"#{e['id']} · {date} · {label}",
            callback_data=f"return_entry:{e['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="📝 Новое (не привязывать)", callback_data="return_entry:0")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(ReturnStates.choosing_entry)
    await message.reply("🔄 К какой записи помощи это относится?", reply_markup=kb)


@router.callback_query(ReturnStates.choosing_entry, F.data.startswith("return_entry:"))
async def choose_entry(callback: CallbackQuery, state: FSMContext):
    entry_id = int(callback.data.split(":")[1])
    await state.update_data(help_entry_id=entry_id if entry_id != 0 else None)
    await state.set_state(ReturnStates.waiting_for_description)
    if entry_id != 0:
        entry = await get_entry_by_id(entry_id)
        preview = entry["text"][:60] if entry else ""
        await callback.message.edit_text(
            f"✨ Запись #{entry_id}: «{preview}»\n\n"
            "Расскажи что вернулось! Можешь прикрепить фото, видео или кружочек."
        )
    else:
        await callback.message.edit_text(
            "✨ Расскажи что вернулось! Можешь прикрепить фото, видео или кружочек."
        )


@router.message(ReturnStates.waiting_for_description)
async def receive_return(message: Message, state: FSMContext):
    user = message.from_user
    data = await state.get_data()
    help_entry_id = data.get("help_entry_id")
    text = message.caption or message.text or ""
    media_id, media_type = None, None
    if message.photo:
        media_id, media_type = message.photo[-1].file_id, "photo"
    elif message.video:
        media_id, media_type = message.video.file_id, "video"
    elif message.video_note:
        media_id, media_type = message.video_note.file_id, "video_note"
    elif message.voice:
        media_id, media_type = message.voice.file_id, "voice"
    if not text and not media_id:
        await message.reply("Напиши что-нибудь или прикрепи медиа 🙏")
        return
    entry = await save_return_entry(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name,
        text=text,
