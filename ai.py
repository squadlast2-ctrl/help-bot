import os
import httpx

_URL   = "https://openrouter.ai/api/v1/chat/completions"
_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type":  "application/json"
    }


async def _ask(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(_URL, headers=_headers(), json={
            "model": _MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user}
            ]
        })
    return r.json()["choices"][0]["message"]["content"]


async def живой_отклик(description: str) -> str:
    return await _ask(
        "Ты тёплый и живой друг. Человек только что помог кому-то и записал это. "
        "Откликнись душевно — 2-3 предложения, без пафоса. По-русски.",
        description)

async def напоминание(name: str, description: str, days: int) -> str:
    return await _ask(
        f"Прошло {days} дней с момента помощи. Мягко спроси у {name} что вернулось. "
        "Коротко, тепло, без давления. По-русски.",
        description)

async def напоминание_тишина(name: str) -> str:
    return await _ask(
        f"Человек по имени {name} давно не записывал добрые дела. "
        "Мягко напомни о боте. Коротко, по-русски.",
        "давно не было записей")

async def летописец(events: list) -> str:
    text = "\n".join(f"- {e['description']}" for e in events)
    return await _ask(
        "Ты летописец добрых дел. Напиши красивую короткую историю по этим записям. "
        "Образно, тепло. По-русски.", text)

async def паттерн_аналитик(events: list) -> str:
    text = "\n".join(f"- {e['description']}" for e in events)
    return await _ask(
        "Найди закономерности в этих добрых делах — кому человек чаще помогает, "
        "в чём его сила. Коротко. По-русски.", text)

async def зеркало(events: list, returns: list) -> str:
    e = "\n".join(f"- {e['description']}" for e in events)
    r = "\n".join(f"- {r['description']}" for r in returns)
    return await _ask(
        "Покажи связь между помощью человека и тем что к нему вернулось. "
        "Мудро и коротко. По-русски.",
        f"Помощь:\n{e}\n\nВернулось:\n{r}")
