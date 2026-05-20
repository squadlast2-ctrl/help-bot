import os
from supabase import create_client, Client
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Подключение ──────────────────────────────────────────────────────────────

def get_db() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)

db: Client = get_db()


# ── Пользователи ─────────────────────────────────────────────────────────────

def get_or_create_user(telegram_id: int, name: str) -> dict:
    """Находит пользователя или создаёт нового."""
    result = db.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if result.data:
        return result.data[0]
    new_user = db.table("users").insert({
        "telegram_id": telegram_id,
        "name": name,
    }).execute()
    return new_user.data[0]


# ── События помощи ───────────────────────────────────────────────────────────

def create_event(user_id: int, description: str, photo_urls: list[str] = None) -> dict:
    """Создаёт новую запись о помощи."""
    event = db.table("events").insert({
        "user_id": user_id,
        "description": description,
        "photo_urls": photo_urls or [],
        "status": "active",
    }).execute()
    return event.data[0]


def get_active_events(user_id: int) -> list[dict]:
    """Все открытые истории пользователя (возврат ещё не записан)."""
    result = db.table("events") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("status", "active") \
        .order("created_at", desc=True) \
        .execute()
    return result.data


def get_events_last_30_days(user_id: int) -> list[dict]:
    """Все события за последние 30 дней вместе с возвратами (для Зеркала)."""
    result = db.table("events") \
        .select("*, returns(*)") \
        .eq("user_id", user_id) \
        .gte("created_at", "now() - interval '30 days'") \
        .execute()
    return result.data


def close_event(event_id: str) -> dict:
    """Закрывает историю когда записан возврат."""
    result = db.table("events") \
        .update({"status": "closed"}) \
        .eq("id", event_id) \
        .execute()
    return result.data[0]


def get_last_event_date(user_id: int) -> datetime | None:
    """Дата последней записи пользователя (для детектора тишины)."""
    result = db.table("events") \
        .select("created_at") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    if not result.data:
        return None
    return datetime.fromisoformat(result.data[0]["created_at"])


# ── Возвраты ─────────────────────────────────────────────────────────────────

def create_return(event_id: str, description: str, photo_urls: list[str] = None) -> dict:
    """Записывает возврат к конкретной истории."""
    ret = db.table("returns").insert({
        "event_id": event_id,
        "description": description,
        "photo_urls": photo_urls or [],
    }).execute()
    close_event(event_id)
    return ret.data[0]


# ── Хранилище фото ───────────────────────────────────────────────────────────

def upload_photo(user_id: int, event_id: str, file_bytes: bytes,
                 filename: str, is_return: bool = False) -> str:
    """
    Загружает фото в Supabase Storage.
    Возвращает публичный URL файла.

    Путь: help-media / user_{id} / event_{id} / [return_] filename
    """
    prefix = "return_" if is_return else ""
    path = f"user_{user_id}/event_{event_id}/{prefix}{filename}"

    db.storage.from_("help-media").upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": "image/jpeg"},
    )

    # Получаем публичную ссылку
    public_url = db.storage.from_("help-media").get_public_url(path)
    return public_url


# ── Напоминания ───────────────────────────────────────────────────────────────

def reminder_already_sent(user_id: int, event_id: str | None, reminder_type: str) -> bool:
    """Проверяет, было ли уже отправлено такое напоминание."""
    query = db.table("reminders") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("type", reminder_type) \
        .eq("sent", True)
    if event_id:
        query = query.eq("event_id", event_id)
    result = query.execute()
    return len(result.data) > 0


def mark_reminder_sent(user_id: int, event_id: str | None, reminder_type: str):
    """Помечает напоминание как отправленное."""
    db.table("reminders").insert({
        "user_id": user_id,
        "event_id": event_id,
        "type": reminder_type,
        "sent": True,
    }).execute()
