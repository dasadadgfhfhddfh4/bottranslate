"""TranslatorBot - Webhook версия для Render."""
import logging
import os
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn

from handlers import router

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
    print("[!] BOT_TOKEN не найден!")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

bot = Bot(
    token=bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Современный способ запуска кода при старте."""
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != webhook_url:
            await bot.set_webhook(url=webhook_url)
            logging.info(f"✅ Webhook установлен: {webhook_url}")
    else:
        logging.error(" WEBHOOK_URL не задан!")
    
    yield  # Здесь приложение работает
    
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("Bot stopped")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def healthcheck():
    """Render проверяет этот эндпоинт"""
    return {"status": "running", "bot": "translator"}


@app.post("/webhook")
async def webhook(request: Request):
    """Принимает обновления от Telegram"""
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}


# ✅ ИСПРАВЛЕНО: добавлены двойные подчёркивания
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)