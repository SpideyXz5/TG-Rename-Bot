"""
Per-spec: thumbnails must NOT survive a bot restart, so this is a plain
in-process dict rather than a Mongo collection. Downloaded thumbnail files
live under config.DOWNLOAD_DIR/thumbs/<user_id>.jpg.
"""
import os
from bot.config import config

_thumbs: dict[int, str] = {}

THUMB_DIR = os.path.join(config.DOWNLOAD_DIR, "thumbs")
os.makedirs(THUMB_DIR, exist_ok=True)


def thumb_path_for(user_id: int) -> str:
    return os.path.join(THUMB_DIR, f"{user_id}.jpg")


def set_thumbnail(user_id: int, file_path: str):
    _thumbs[user_id] = file_path


def get_thumbnail(user_id: int) -> str | None:
    path = _thumbs.get(user_id)
    if path and os.path.exists(path):
        return path
    return None


def delete_thumbnail(user_id: int):
    path = _thumbs.pop(user_id, None)
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
