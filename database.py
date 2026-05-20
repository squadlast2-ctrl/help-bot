import os
from supabase import create_client
from datetime import datetime, timedelta


def get_db():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


# ─── ПОЛЬЗОВАТЕЛИ ────────────────────────────────────────────────────────────

def save_user(telegram_id: int, name: str):
    get_db().table("users").upsert(
        {"telegram_id": telegram_id, "name": name},
        on_conflict="telegram_id"
    ).execute()


def get_user(telegram_id: int) -> dict | None:
    res = get_db().table("users").select("*").eq("telegram_id", telegram_id).execute()
    return res.data[0] if res.data else None


# ─── СОБЫТИЯ ПОМОЩИ ───────────────────────────────────────────────────────────

def save_event(telegram_id: int, description: str, photo_urls: list = []) -> str:
    db = get_db()
    res = db.table("events").insert({
        "user_id":     telegram_id,
        "description": description,
        "photo_urls":  photo_urls,
        "status":      "active"
    }).execute()

    event_id = res.data[0]["id"]

    for reminder_type in ["day_30", "day_60", "day_90"]:
        db.table("reminders").insert({
            "user_id":  telegram_id,
            "event_id": event_id,
            "type":     reminder_type,
            "sent":     False
        }).execute()

    return event_id


def get_active_events(telegram_id: int) -> list:
    return get_db().table("events").select("*")\
        .eq("user_id", telegram_id)\
        .eq("status", "active")\
        .order("created_at").execute().data


def get_all_events(telegram_id: int) -> list:
    return get_db().table("events").select("*")\
        .eq("user_id", telegram_id)\
        .order("created_at").execute().data


def close_event(event_id: str):
    get_db().table("events").update({"status": "closed"})\
        .eq("id", event_id).execute()


# ─── ВОЗВРАТЫ ─────────────────────────────────────────────────────────────────

def save_return(telegram_id: int, description: str, photo_urls: list = []) -> str | None:
    events = get_active_events(telegram_id)
    if not events:
        return None
    event = events[0]
    get_db().table("returns").insert({
        "event_id":    event["id"],
        "description": description,
        "photo_urls":  photo_urls
    }).execute()
    close_event(event["id"])
    return event["id"]


def get_all_returns(telegram_id: int) -> list:
    events = get_all_events(telegram_id)
    if not events:
        return []
    event_ids = [e["id"] for e in events]
    return get_db().table("returns").select("*")\
        .in_("event_id", event_ids).execute().data


# ─── СТАТИСТИКА ───────────────────────────────────────────────────────────────

def get_stats(telegram_id: int) -> dict:
    events  = get_all_events(telegram_id)
    returns = get_all_returns(telegram_id)
    active  = [e for e in events if e["status"] == "active"]
    return {
        "total_events":  len(events),
        "total_returns": len(returns),
        "active_events": len(active),
        "closed_events": len(events) - len(active)
    }


# ─── НАПОМИНАНИЯ ──────────────────────────────────────────────────────────────

def get_pending_reminders() -> list:
    OFFSETS = {"day_30": 30, "day_60": 60, "day_90": 90}
    res = get_db().table("reminders")\
        .select("*, events(*), users(*)")\
        .eq("sent", False)\
        .in_("type", ["day_30", "day_60", "day_90"])\
        .execute()

    now = datetime.utcnow()
    due = []
    for rem in res.data:
        event = rem.get("events")
        if not event:
            continue
        created_at = datetime.fromisoformat(
            event["created_at"].replace("Z", "").replace("+00:00", "")
        )
        days = OFFSETS.get(rem["type"], 999)
        if now >= created_at + timedelta(days=days):
            due.append(rem)
    return due


def get_pending_silence_reminders() -> list:
    two_days_ago = (datetime.utcnow() - timedelta(days=2)).isoformat()
    db = get_db()
    old_events = db.table("events").select("*, users(*)")\
        .eq("status", "active")\
        .lt("created_at", two_days_ago)\
        .execute().data

    due = []
    for event in old_events:
        existing = db.table("reminders").select("id")\
            .eq("event_id", event["id"])\
            .eq("type", "silence_2d")\
            .execute().data
        if not existing:
            due.append(event)
            db.table("reminders").insert({
                "user_id":  event["user_id"],
                "event_id": event["id"],
                "type":     "silence_2d",
                "sent":     True
            }).execute()
    return due


def mark_reminder_sent(reminder_id: str):
    get_db().table("reminders").update({"sent": True})\
        .eq("id", reminder_id).execute()
