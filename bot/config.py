"""
Central configuration loaded from environment variables.
Never hardcode credentials — everything comes from .env / the host's env panel.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Required ---
    BOT_TOKEN: str = os.environ["BOT_TOKEN"]
    MONGO_URI: str = os.environ["MONGO_URI"]
    OWNER_ID: int = _env_int("OWNER_ID")

    # --- Optional ---
    DB_NAME: str = os.environ.get("DB_NAME", "rename_bot")
    DOWNLOAD_DIR: str = os.environ.get("DOWNLOAD_DIR", "./downloads")

    # Developer credit — must never be removed/changed per project spec.
    DEVELOPER_CREDIT: str = "@SpideyXz5"

    # File size limits (bytes)
    NORMAL_MAX_FILE_SIZE: int = 2 * 1024 * 1024 * 1024   # 2 GB
    OWNER_MAX_FILE_SIZE: int = 4 * 1024 * 1024 * 1024    # 4 GB

    # Queue limits
    MAX_QUEUE_SIZE: int = 20
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5

    # Verification durations shown to admin (label -> seconds)
    VERIFY_DURATIONS = {
        "30m": 30 * 60,
        "1h": 60 * 60,
        "3h": 3 * 60 * 60,
        "6h": 6 * 60 * 60,
        "12h": 12 * 60 * 60,
        "24h": 24 * 60 * 60,
    }

    # Progress-bar edit throttle (seconds) to avoid Telegram flood limits
    PROGRESS_EDIT_INTERVAL: int = 4


config = Config()

os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
