import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from bot.config import get_settings
from bot.handlers import router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)


def get_bot_token() -> str | None:
    try:
        settings = get_settings()
        return settings.bot_token.get_secret_value()
    except Exception:
        return os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")


TOKEN = get_bot_token()

if not TOKEN:
    logging.error("BOT_TOKEN not found. Set BOT_TOKEN in environment or .env")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) if TOKEN else None

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

app = FastAPI(title="BotTranslate", version="1.0.0")
app.state.polling_task = None


async def start_polling() -> None:
    if not bot:
        return
    if app.state.polling_task and not app.state.polling_task.done():
        return
    app.state.polling_task = asyncio.create_task(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), skip_updates=True)
    )


@app.on_event("startup")
async def startup_event() -> None:
    if not bot:
        logging.error("Bot was not started because TOKEN is missing")
        return
    logging.info("Starting bot polling from web app startup")
    await start_polling()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if app.state.polling_task:
        app.state.polling_task.cancel()
    if bot:
        await bot.session.close()


@app.get("/health")
async def health() -> JSONResponse:
    if not bot:
        return JSONResponse(status_code=503, content={"status": "error", "detail": "BOT_TOKEN missing"})
    return JSONResponse(status_code=200, content={"status": "ok", "bot": "running"})


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "BotTranslate is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
