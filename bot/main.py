import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем твои хендлеры (убедись, что файл handlers.py существует)
from bot.handlers import router

# Загружаем переменные из .env файла
load_dotenv()

# --- 1. Конфигурация и инициализация ---

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("❌ [!] BOT_TOKEN не найден! Создай файл .env и добавь туда BOT_TOKEN=твой_токен")
    sys.exit(1)

# Настраиваем логирование, чтобы видеть, что происходит
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)

# Создаём объект бота
bot = Bot(
    token=bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаём диспетчер с хранилищем в памяти (FSM будет работать, пока бот запущен)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем маршруты (хендлеры)
dp.include_router(router)


# --- 2. Точка входа (Асинхронная функция main) ---

async def main():
    """Главная функция, которая запускает бота."""
    logging.info("🚀 Запуск бота в режиме Polling...")
    
    # skip_updates=True означает, что бот проигнорирует сообщения, 
    # которые были отправлены ему, пока он был выключен.
    # Это очень полезно, чтобы не спамить старыми сообщениями при каждом перезапуске.
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), skip_updates=True)
    finally:
        # Корректное закрытие сессии при остановке (Ctrl+C)
        await bot.session.close()
        logging.info("🛑 Бот остановлен, сессии закрыты.")


# --- 3. Запуск ---

if __name__ == "__main__":
    try:
        # asyncio.run() создаёт event loop и запускает нашу асинхронную функцию main()
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Эти исключения срабатывают, когда ты нажимаешь Ctrl+C в терминале.
        # Мы их ловим, чтобы не вываливать страшный traceback в консоль.
        logging.info("👋 Бот остановлен пользователем (Ctrl+C).")