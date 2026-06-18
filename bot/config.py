# config.py
from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация Telegram-бота.
    Читает переменные из окружения и файла .env
    """
    
    # 🔐 Токен бота. Используем SecretStr для безопасности!
    # Если в логах случайно выведется settings, токен будет скрыт звездочками.
    bot_token: SecretStr = Field(
        ..., 
        alias="BOT_TOKEN",
        min_length=40,  # Telegram-токены длинные, это базовая защита от опечаток
        description="Telegram Bot Token from @BotFather"
    )
    
    # 🛠 Дополнительные настройки (пример расширяемости)
    admin_ids: list[int] = Field(default=[], description="ID администраторов бота")
    webhook_url: str | None = Field(default=None, description="URL для вебхука (если не используем polling)")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",  # Игнорируем переменные из .env, которых нет в классе
    )


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    """
    Кэшированный геттер настроек.
    
    ВАЖНО: lru_cache гарантирует, что .env файл будет прочитан ТОЛЬКО ОДИН РАЗ.
    В асинхронных приложениях (как aiogram) это критично для производительности.
    """
    return Settings()