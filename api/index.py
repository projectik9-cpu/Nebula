"""
Serverless функция для обработки вебхуков Telegram
Деплой на Vercel
"""
import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from config_serverless import (
    BOT_TOKEN, 
    WEBHOOK_URL, 
    WEBHOOK_PATH,
    ADMIN_CHAT_ID,
    REFERRAL_REWARD
)
from database_serverless import Database
from handlers import register_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация
app = FastAPI()
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

# Регистрируем обработчики
register_handlers(dp, bot, db)

logger.info("Bot initialized for serverless")


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    """Обработка вебхуков от Telegram"""
    try:
        # Получаем данные от Telegram
        data = await request.json()
        logger.info(f"Received webhook: {data}")
        
        # Создаём Update объект
        update = types.Update(**data)
        
        # Обрабатываем апдейт
        await dp.feed_update(bot, update)
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/")
async def root():
    """Корневой путь"""
    return {
        "status": "running",
        "bot": "Referral Bot",
        "version": "3.0 Serverless"
    }


@app.get("/set_webhook")
async def setup_webhook():
    """Установка вебхука (вызывается один раз после деплоя)"""
    try:
        webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        
        # Удаляем старый вебхук
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Old webhook deleted")
        
        # Устанавливаем новый
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        # Проверяем
        webhook_info = await bot.get_webhook_info()
        
        logger.info(f"Webhook set to: {webhook_url}")
        
        return {
            "status": "success",
            "webhook_url": webhook_url,
            "webhook_info": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
            }
        }
    
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/webhook_info")
async def get_webhook_info():
    """Получить информацию о текущем вебхуке"""
    try:
        webhook_info = await bot.get_webhook_info()
        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/health")
async def health_check():
    """Проверка здоровья бота"""
    try:
        # Проверяем подключение к боту
        bot_info = await bot.get_me()
        
        # Проверяем подключение к базе данных
        db_status = db.health_check()
        
        return {
            "status": "healthy",
            "bot": {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name
            },
            "database": db_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            {"status": "unhealthy", "error": str(e)},
            status_code=500
        )


# Для локальной разработки
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
