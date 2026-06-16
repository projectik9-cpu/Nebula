"""
Конфигурация для Serverless деплоя
Все настройки берутся из переменных окружения
"""
import os

# Токен бота (ОБЯЗАТЕЛЬНО!)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# ID администратора (ОБЯЗАТЕЛЬНО!)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if ADMIN_CHAT_ID:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
else:
    raise ValueError("ADMIN_CHAT_ID environment variable is not set!")

# URL вашего деплоя на Vercel (ОБЯЗАТЕЛЬНО!)
# Пример: https://your-bot.vercel.app
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable is not set!")

# Путь для вебхука (секретный, используем токен для безопасности)
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# Награда за реферала
REFERRAL_REWARD = float(os.getenv("REFERRAL_REWARD", "5.0"))

# База данных PostgreSQL (ОБЯЗАТЕЛЬНО!)
# Пример: postgresql://user:password@host:5432/database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Анти-спам настройки
SPAM_COOLDOWN = float(os.getenv("SPAM_COOLDOWN", "1.0"))

# Режим разработки
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
