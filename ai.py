import httpx
from config import OPENROUTER_API_KEY

_URL   = "https://openrouter.ai/api/v1/chat/completions"
_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
_HDR   = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type":  "application/json"
}


async def _ask(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(_URL, headers=_HDR, json={
            "model": _MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user}
            ]
        })
    data = r.json()
    return data["choices"][0]["message"]["content"]


# ─── 5 ролей ИИ ───────────────────────────────────────────────────────────────

async def живой_отклик(description: str) -> str:
    """Тёплый отклик когда человек записал помощь."""
    return await _ask(
        "Ты тёплый и живой друг. Человек только что помог кому-то "
        "и записал это. Откликнись душевно — 2-3 предложения, "
        "без пафоса и шаблонов. Пиши по-русски.",
        description
    )


async def напоминание(name: str, description: str, days: int) -> str:
    """Мягкое напоминание спросить о возврате."""
    return await _ask(
        f"Прошло {days} дней с момента помощи. Мягко и тепло напомни "
        f"человеку по имени {name} — как дела? что вернулось? "
        "Без давления, коротко. По-русски.",
        description
    )


async def напоминание_тишина(name: str) -> str:
    """Напоминание если человек давно не писал."""
    return await _ask(
        "Человек давно не записывал добрые дела. Мягко и тепло "
        "напомни ему о боте — может что-то происходило хорошего? "
        f"Обращайся по имени: {name}. Коротко, по-русски.",
        "давно не было записей"
    )


async def летописец(events: list) -> str:
    """Красивая история из всех добрых дел."""
    text = "\n".join(f"- {e['description']}" for e in events)
    return await _ask(
        "Ты летописец добрых дел. На основе этих записей напиши "
        "красивую короткую историю — образно, тепло, вдохновляюще. "
        "По-русски.",
        text
    )


async def паттерн_аналитик(events: list) -> str:
    """Находит закономерности в добрых делах."""
    text = "\n".join(f"- {e['description']}" for e in events)
    return await _ask(
        "Ты аналитик паттернов. Найди закономерности и темы "
        "в этих добрых делах — кому человек чаще помогает, "
        "в чём его сила. Коротко и точно. По-русски.",
        text
    )


async def зеркало(events: list, returns: list) -> str:
    """Показывает связь между помощью и возвратами."""
    e_text = "\n".join(f"- {e['description']}" for e in events)
    r_text = "\n".join(f"- {r['description']}" for r in returns)
    return await _ask(
        "Ты мудрое зеркало. Покажи человеку связь между его помощью "
        "и тем что к нему вернулось. Тепло, образно, без мистики. "
        "По-русски.",
        f"Помощь:\n{e_text}\n\nВернулось:\n{r_text}"
    )
