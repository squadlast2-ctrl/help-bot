import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def ask_ai(system_prompt: str, user_content: str, max_tokens: int = 1000) -> str:
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/help_bot",
        "X-Title": "Help Bot",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def generate_story(helps: list[dict], returns: list[dict], period_days: int) -> str:
    system = (
        "Ты — мудрый наблюдатель, который помогает людям увидеть красоту и смысл "
        "в их добрых делах. Пиши тепло, вдохновляюще, на русском языке. "
        "Не перечисляй записи механически — создай живой нарратив с паттернами, "
        "инсайтами и вдохновением. Максимум 400 слов."
    )
    helps_text = "\n".join(
        f"- {h['full_name']}: {h['text']} [{h['created_at'][:10]}]" for h in helps
    )
    returns_text = "\n".join(
        f"- {r['full_name']}: {r['text']} [{r['created_at'][:10]}]" for r in returns
    )
    user_content = (
        f"Вот что происходило в нашей группе за последние {period_days} дней.\n\n"
        f"ПОМОЩЬ ({len(helps)} записей):\n{helps_text or 'Нет записей'}\n\n"
        f"ЧТО ВЕРНУЛОСЬ ({len(returns)} записей):\n{returns_text or 'Нет записей'}\n\n"
        "Напиши вдохновляющую историю об этом периоде. "
        "Найди паттерны, отметь кто особенно активен, покажи связь между помощью и возвратами."
    )
    return await ask_ai(system, user_content, max_tokens=600)


async def generate_reminder() -> str:
    system = (
        "Ты — тёплый и живой участник группы взаимопомощи. "
        "Пиши коротко (2-3 предложения), по-человечески, на русском. "
        "Иногда с лёгким юмором, иногда с теплотой. Не будь занудным."
    )
    user_content = (
        "В группе уже несколько дней тишина. Напиши короткое напоминание-приглашение "
        "поделиться — кому помогли сегодня или что хорошего произошло. "
        "Каждый раз немного по-другому, не повторяй одни и те же фразы."
    )
    return await ask_ai(system, user_content, max_tokens=150)


async def analyze_patterns(helps: list[dict], returns: list[dict]) -> str:
    system = (
        "Ты — аналитик паттернов доброты. Анализируй кратко и по делу. "
        "Русский язык. Максимум 200 слов."
    )
    user_content = (
        f"Проанализируй {len(helps)} записей помощи и {len(returns)} возвратов. "
        f"Найди: 1) самые частые темы помощи, 2) среднее время между помощью и возвратом, "
        f"3) кто в группе помогает чаще всего, 4) неожиданные паттерны.\n\n"
        f"Помощь: {[h['text'][:100] for h in helps[:20]]}\n"
        f"Возвраты: {[r['text'][:100] for r in returns[:20]]}"
    )
    return await ask_ai(system, user_content, max_tokens=300)
