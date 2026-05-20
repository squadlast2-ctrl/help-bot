from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


# ──────────────────────────────────────────────
# ПОМОЩЬ
# ──────────────────────────────────────────────

async def save_help_entry(
    user_id: int,
    username: str,
    full_name: str,
    text: str,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None,  # photo | video | voice | document
) -> dict:
    db = get_db()
    data = {
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "text": text,
        "media_url": media_url,
        "media_type": media_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_closed": False,
    }
    result = db.table("help_entries").insert(data).execute()
    return result.data[0]


async def get_open_entries(user_id: int) -> list[dict]:
    db = get_db()
    result = (
        db.table("help_entries")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_closed", False)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


async def get_entry_by_id(entry_id: int) -> Optional[dict]:
    db = get_db()
    result = db.table("help_entries").select("*").eq("id", entry_id).execute()
    return result.data[0] if result.data else None


async def close_entry(entry_id: int) -> None:
    db = get_db()
    db.table("help_entries").update({"is_closed": True}).eq("id", entry_id).execute()


# ──────────────────────────────────────────────
# ВОЗВРАТЫ
# ──────────────────────────────────────────────

async def save_return_entry(
    user_id: int,
    username: str,
    full_name: str,
    text: str,
    help_entry_id: Optional[int] = None,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None,
) -> dict:
    db = get_db()
    data = {
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "text": text,
        "help_entry_id": help_entry_id,
        "media_url": media_url,
        "media_type": media_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.table("return_entries").insert(data).execute()
    if help_entry_id:
        await close_entry(help_entry_id)
    return result.data[0]


# ──────────────────────────────────────────────
# СТАТИСТИКА
# ──────────────────────────────────────────────

async def get_stats_for_user(user_id: int, days: int) -> dict:
    db = get_db()
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    helps = (
        db.table("help_entries")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", since)
        .execute()
    )
    returns = (
        db.table("return_entries")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", since)
        .execute()
    )
    return {"helps": helps.data, "returns": returns.data}


async def get_group_stats(days: int) -> dict:
    db = get_db()
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    helps = (
        db.table("help_entries")
        .select("*")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
    )
    returns = (
        db.table("return_entries")
        .select("*")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
    )
    return {"helps": helps.data, "returns": returns.data}


# ──────────────────────────────────────────────
# НАПОМИНАНИЯ — последняя активность в группе
# ──────────────────────────────────────────────

async def get_last_activity_date() -> Optional[datetime]:
    db = get_db()
    result = (
        db.table("help_entries")
        .select("created_at")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return datetime.fromisoformat(result.data[0]["created_at"])
    return None
