from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    SUPABASE_URL: str
    SUPABASE_KEY: str
    GROUP_CHAT_ID: int  # ID вашей Telegram-группы (отрицательное число)
    REMINDER_SILENCE_DAYS: int = 2  # через сколько дней молчания напоминать

    class Config:
        env_file = ".env"


settings = Settings()
