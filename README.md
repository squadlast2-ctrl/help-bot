# 🤝 Бот «Помощь» — инструкция по запуску

## Что умеет бот
- `/помог` — записать кому помог (текст + фото/видео/кружочек)
- `/вернулось` — записать что хорошего вернулось
- `/стата`, `/стата60`, `/стата90` — личная статистика
- `/группа` — статистика всей группы
- `/история` — ИИ пишет вдохновляющую историю месяца
- `/история90` — история за 90 дней
- `/паттерны` — ИИ анализирует паттерны группы
- Автонапоминание если группа молчит 2+ дня
- Автоматическая история 1-го числа каждого месяца

---

## Шаг 1 — Создать бота в Telegram

1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Напиши `/newbot`
3. Придумай название: `Помощь`
4. Придумай username: `help_your_name_bot`
5. Скопируй **токен** — он выглядит как `1234567890:ABCdef...`

---

## Шаг 2 — Создать базу данных в Supabase

1. Зайди на [supabase.com](https://supabase.com) → Sign Up
2. New Project → придумай название и пароль
3. Подожди ~1 минуту пока создаётся
4. Зайди в **SQL Editor** → **New query**
5. Скопируй содержимое файла `supabase_schema.sql` и нажми **Run**
6. Зайди в **Settings → API**:
   - Скопируй **Project URL** → это `SUPABASE_URL`
   - Скопируй **service_role** secret key → это `SUPABASE_KEY`
   
   ⚠️ Используй именно `service_role`, не `anon`!

---

## Шаг 3 — Получить ключ OpenRouter

1. Зайди на [openrouter.ai](https://openrouter.ai) → Sign In
2. Keys → Create Key
3. Скопируй ключ → это `OPENROUTER_API_KEY`
4. Пополни баланс на $5 (хватит на месяцы работы)

Рекомендуемая модель: `anthropic/claude-3.5-sonnet` (умная, недорогая)
Дешевле: `mistralai/mistral-7b-instruct` (почти бесплатно)

---

## Шаг 4 — Узнать ID группы

1. Добавь бота [@userinfobot](https://t.me/userinfobot) в свою группу
2. Напиши в группе `/start@userinfobot`
3. Он ответит ID группы — это отрицательное число типа `-1001234567890`
4. Это твой `GROUP_CHAT_ID`

Не забудь: **добавь своего бота в группу** и **сделай его администратором**!

---

## Шаг 5 — Задеплоить на Railway

1. Зайди на [railway.app](https://railway.app) → Login with GitHub
2. **New Project → Deploy from GitHub repo**
   - Или используй **New Project → Empty Project → Add Service → GitHub Repo**
3. Загрузи файлы проекта в GitHub (или сделай через Railway CLI)
4. В Railway зайди в свой сервис → **Variables** → добавь все переменные:

```
TELEGRAM_TOKEN=1234567890:ABCdef...
GROUP_CHAT_ID=-1001234567890
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
REMINDER_SILENCE_DAYS=2
```

5. Railway автоматически задеплоит бота. Зайди в **Logs** и убедись что написано `Бот запущен ✅`

---

## Альтернатива — запустить локально (для теста)

```bash
# 1. Установить Python 3.11+
# 2. Клонировать проект и зайти в папку

pip install -r requirements.txt

# Создать файл .env (скопировать из .env.example и заполнить)
cp .env.example .env

python bot.py
```

---

## Структура файлов

```
help_bot/
├── bot.py              # точка входа
├── config.py           # переменные окружения
├── database.py         # все запросы к Supabase
├── ai_client.py        # запросы к OpenRouter
├── scheduler.py        # напоминания и автоистории
├── handlers/
│   ├── help_handler.py    # /помог
│   ├── return_handler.py  # /вернулось
│   ├── stats_handler.py   # /стата, /история, /паттерны
│   └── admin_handler.py   # /start, /помощь
├── supabase_schema.sql # SQL для создания таблиц
├── requirements.txt
├── Procfile            # для Railway
└── .env.example        # шаблон переменных
```

---

## Часто задаваемые вопросы

**Бот не отвечает в группе** — убедись что он добавлен в группу и является администратором.

**Ошибка Supabase** — проверь что используешь `service_role` ключ, не `anon`.

**ИИ не генерирует тексты** — проверь баланс на OpenRouter и правильность ключа.

**Как поменять модель** — в переменной `OPENROUTER_MODEL` укажи другую, например `openai/gpt-4o` или `mistralai/mistral-7b-instruct`.
