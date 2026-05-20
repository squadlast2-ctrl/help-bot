import os
import json
from datetime import datetime
import google.generativeai as genai

# ── Подключение к Gemini ──────────────────────────────────────────────────────
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")


def _ask(prompt: str, max_tokens: int = 300) -> str:
    """Базовый запрос к Gemini. Все роли используют эту функцию."""
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
    )
    return response.text.strip()


# ── Роль 1: Живой отклик ──────────────────────────────────────────────────────

async def get_live_response(description: str, user_id: int, has_photo: bool) -> str:
    """
    Срабатывает каждый раз когда пользователь записывает помощь.
    Возвращает одну живую небанальную фразу.
    """
    from database import db

    # Берём последние 3 записи для контекста
    recent = db.table("events") \
        .select("description") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(3) \
        .execute()

    recent_list = [e["description"] for e in recent.data] if recent.data else []
    recent_text = "\n".join(f"- {d}" for d in recent_list) if recent_list else "это первая запись"

    prompt = f"""Ты тёплый наблюдатель за добрыми делами. Пользователь только что записал помощь.

Что он сделал: {description}
Приложил фото: {"да" if has_photo else "нет"}
Его последние записи:
{recent_text}

Ответь ОДНОЙ короткой живой фразой — не шаблонной, не пафосной.
Учти именно эту конкретную ситуацию.
Без восклицательных знаков. Без "молодец". Без "это прекрасно".
Максимум 20 слов. Только русский язык."""

    return _ask(prompt, max_tokens=60)


# ── Роль 2: Паттерн-аналитик ─────────────────────────────────────────────────

async def get_pattern_insight(user_id: int) -> str | None:
    """
    Срабатывает раз в неделю по расписанию.
    Анализирует паттерны и возвращает 3-4 предложения инсайта.
    """
    from database import get_events_last_30_days

    events = get_events_last_30_days(user_id)
    if len(events) < 3:
        return None  # мало данных — молчим

    events_for_ai = [
        {
            "description": e["description"],
            "date": e["created_at"][:10],
            "status": e["status"],
            "return": e["returns"][0]["description"] if e.get("returns") else None,
        }
        for e in events
    ]

    prompt = f"""Вот события помощи пользователя за последнее время:
{json.dumps(events_for_ai, ensure_ascii=False, indent=2)}

Найди 1-2 неочевидных паттерна:
- Кому он помогает чаще?
- Сколько дней в среднем до возврата?
- Есть ли связь между типом помощи и скоростью возврата?

Ответь 3-4 предложениями, как умный друг — не как аналитический отчёт.
Без заголовков. Без списков. Только русский язык."""

    return _ask(prompt, max_tokens=150)


# ── Роль 3: Летописец ────────────────────────────────────────────────────────

async def get_narrator_story(event_id: str, user_id: int) -> str:
    """
    Срабатывает когда история закрыта (записан возврат).
    Генерирует красивую историю + сохраняет сценарий для анимации.
    """
    from database import db

    # Берём событие с возвратом
    event = db.table("events") \
        .select("*, returns(*)") \
        .eq("id", event_id) \
        .single() \
        .execute()

    e = event.data
    helped_at = datetime.fromisoformat(e["created_at"])
    ret = e["returns"][0] if e.get("returns") else None
    returned_at = datetime.fromisoformat(ret["created_at"]) if ret else None
    days = (returned_at - helped_at).days if returned_at else None

    prompt = f"""История помощи завершена. Данные:

Что сделал: {e["description"]}
Дата помощи: {helped_at.strftime("%d.%m.%Y")}
Что вернулось: {ret["description"] if ret else "не указано"}
Через сколько дней: {days if days else "неизвестно"}

Напиши красивую короткую историю (4-5 предложений).
Стиль: тёплый, немного философский, без пафоса.
Без заголовков. Только русский язык."""

    story = _ask(prompt, max_tokens=200)

    # Сохраняем сценарий для будущей анимации в базу
    scenario = {
        "scene_1": {"date": helped_at.strftime("%d.%m.%Y"), "text": e["description"]},
        "pause": f"{days} дней" if days else "...",
        "scene_2": {"date": returned_at.strftime("%d.%m.%Y") if returned_at else "", "text": ret["description"] if ret else ""},
        "final_phrase": story.split(".")[-2] if "." in story else story[:50],
    }

    db.table("events").update({"animation_scenario": json.dumps(scenario, ensure_ascii=False)}) \
        .eq("id", event_id).execute()

    return story


# ── Роль 4: Напоминатор ───────────────────────────────────────────────────────

async def get_silence_reminder() -> str:
    """Срабатывает когда пользователь молчит 2+ дня."""
    prompt = """Пользователь не записывал добрые дела уже 2 дня.
Напомни о себе одной фразой.
Не нудно, не давящая. Можно с лёгкой иронией.
Максимум 15 слов. Без восклицательных знаков. Только русский язык."""

    return _ask(prompt, max_tokens=40)


async def get_followup_reminder(event_description: str, days_passed: int) -> str:
    """Срабатывает через 30/60/90 дней после записи помощи."""
    prompt = f"""Прошло {days_passed} дней с момента когда пользователь помог:
"{event_description}"

Спроси мягко — случилось ли что-то неожиданно хорошее с тех пор.
Не объясняй концепцию возврата. Просто спроси как друг.
Максимум 20 слов. Без восклицательных знаков. Только русский язык."""

    return _ask(prompt, max_tokens=50)


# ── Роль 5: Зеркало ───────────────────────────────────────────────────────────

async def get_mirror_insight(user_id: int) -> str | None:
    """
    Срабатывает раз в месяц по расписанию.
    Составляет 'профиль помощника' пользователя.
    """
    from database import get_events_last_30_days

    events = get_events_last_30_days(user_id)
    if not events:
        return None

    # Считаем статистику здесь — не тратим токены на математику
    total = len(events)
    closed = [e for e in events if e["status"] == "closed"]

    return_days_list = []
    for e in closed:
        if e.get("returns"):
            helped_at = datetime.fromisoformat(e["created_at"])
            returned_at = datetime.fromisoformat(e["returns"][0]["created_at"])
            return_days_list.append((returned_at - helped_at).days)

    avg_days = round(sum(return_days_list) / len(return_days_list)) if return_days_list else None

    events_for_ai = [
        {
            "description": e["description"],
            "date": e["created_at"][:10],
            "status": e["status"],
            "return": e["returns"][0]["description"] if e.get("returns") else None,
        }
        for e in events
    ]

    prompt = f"""Вот все данные пользователя за последние 30 дней:

Всего помощей: {total}
Закрытых историй: {len(closed)}
Среднее дней до возврата: {avg_days if avg_days else "нет данных"}
События:
{json.dumps(events_for_ai, ensure_ascii=False, indent=2)}

Составь его профиль помощника. Структура:
1. Одна фраза-заголовок месяца (ёмко, неожиданно)
2. Цифры поданные как история, не как таблица (2-3 предложения)
3. Самая сильная история месяца — пересказать тепло (2 предложения)
4. Один инсайт о человеке — что ты заметил в нём как в личности

Тон: как будто лучший друг рассказывает тебе о тебе за чашкой кофе.
Без пафоса. Без "ты молодец". Без восклицательных знаков.
Не больше 150 слов. Только русский язык."""

    return _ask(prompt, max_tokens=400)
