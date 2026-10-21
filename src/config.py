"""Конфигурация бота.

Все токены и настройки читаются из переменных окружения (.env), а не из кода.
Скопируйте .env.example в .env и заполните значения.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_list(name: str) -> list:
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
TELEGRAM_API_ID = _env_int("TELEGRAM_API_ID", 0)
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")

# --- Интервалы ---
POST_INTERVAL_MINUTES = _env_int("POST_INTERVAL_MINUTES", 60)
PUBLISH_INTERVAL_MINUTES = _env_int("PUBLISH_INTERVAL_MINUTES", 30)
MAX_POSTS_PER_COLLECT = _env_int("MAX_POSTS_PER_COLLECT", 20)
MEME_PROBABILITY = _env_float("MEME_PROBABILITY", 0.4)

# --- Источники контента ---
SOURCE_CHANNELS = _env_list("SOURCE_CHANNELS")
RSS_FEEDS = _env_list("RSS_FEEDS")

# --- Файлы состояния (рядом с кодом, независимо от текущей директории) ---
HISTORY_FILE = str(BASE_DIR / "posted_history.json")
QUEUE_FILE = str(BASE_DIR / "queue.json")
SESSION_FILE = str(BASE_DIR / "user_session.session")


def validate() -> None:
    """Проверяет, что заданы обязательные переменные окружения."""
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
            ("CHANNEL_ID", CHANNEL_ID),
            ("TELEGRAM_API_HASH", TELEGRAM_API_HASH),
        )
        if not value
    ]
    if not TELEGRAM_API_ID:
        missing.append("TELEGRAM_API_ID")

    if missing:
        raise SystemExit(
            "Не заданы переменные окружения: "
            + ", ".join(missing)
            + "\nСкопируйте .env.example в .env и заполните значения."
        )
