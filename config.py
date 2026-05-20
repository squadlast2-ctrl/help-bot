import os

def get_config():
    return {
        "TELEGRAM_BOT_TOKEN": os.environ["TELEGRAM_BOT_TOKEN"],
        "SUPABASE_URL":       os.environ["SUPABASE_URL"],
        "SUPABASE_KEY":       os.environ["SUPABASE_KEY"],
        "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
        "GROUP_ID":           int(os.environ.get("GROUP_ID", "0")),
        "TOPIC_HELP":         int(os.environ.get("TOPIC_HELP", "0")),
        "TOPIC_RETURN":       int(os.environ.get("TOPIC_RETURN", "0")),
        "TOPIC_GENERAL":      int(os.environ.get("TOPIC_GENERAL", "0")),
    }

# Удобные геттеры
def TOKEN():           return os.environ["TELEGRAM_BOT_TOKEN"]
def GROUP_ID():        return int(os.environ.get("GROUP_ID", "0"))
def TOPIC_HELP():      return int(os.environ.get("TOPIC_HELP", "0"))
def TOPIC_RETURN():    return int(os.environ.get("TOPIC_RETURN", "0"))
def TOPIC_GENERAL():   return int(os.environ.get("TOPIC_GENERAL", "0"))
def OPENROUTER_KEY():  return os.environ["OPENROUTER_API_KEY"]
