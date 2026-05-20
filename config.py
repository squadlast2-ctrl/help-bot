import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_KEY       = os.environ["SUPABASE_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

GROUP_ID      = int(os.environ.get("GROUP_ID", "0"))
TOPIC_HELP    = int(os.environ.get("TOPIC_HELP", "0"))
TOPIC_RETURN  = int(os.environ.get("TOPIC_RETURN", "0"))
TOPIC_GENERAL = int(os.environ.get("TOPIC_GENERAL", "0"))
