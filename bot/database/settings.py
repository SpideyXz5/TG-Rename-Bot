"""
Generic settings document. Single document with _id="config" holding every
toggle/value the admin can configure through inline buttons.
Defaults live here so a fresh deployment works out of the box.
"""
from bot.database.mongo import settings_col

_DEFAULTS = {
    "_id": "config",

    # Welcome
    "welcome_photo": None,
    "welcome_message": (
        "Hi {mention}!\n\n"
        "Send me any file and I'll rename it for you.\n\n"
        f"Developer: @SpideyXz5"
    ),

    # Bot settings
    "maintenance": False,
    "public_usage": True,
    "log_channel": None,
    "dub_channel": None,

    # Shortener
    "shortener_enabled": False,
    "shortener_domain": None,
    "shortener_api": None,
    "shortener_duration": 3 * 60 * 60,  # default 3h, seconds

    # Rename settings
    "auto_rename_enabled": False,
    "rename_format": "{title} S{season}E{episode} [{quality}] {audio}",
    "caption": (
        "<b>{filename}</b>\n"
        "Size: {filesize}\n"
        "Requested by: {user}"
    ),
    "video_format": "video",     # video | document
    "document_format": "document",
    "loading_animation": True,

    # Metadata
    "metadata_enabled": False,
    "metadata_video": "",
    "metadata_audio": "",
    "metadata_subtitle": "",
}

_cache = None


async def _load():
    global _cache
    doc = await settings_col.find_one({"_id": "config"})
    if doc is None:
        doc = dict(_DEFAULTS)
        await settings_col.insert_one(doc)
    else:
        # backfill any new default keys added since this doc was created
        missing = {k: v for k, v in _DEFAULTS.items() if k not in doc}
        if missing:
            await settings_col.update_one({"_id": "config"}, {"$set": missing})
            doc.update(missing)
    _cache = doc
    return doc


async def get_settings() -> dict:
    global _cache
    if _cache is None:
        await _load()
    return _cache


async def set_setting(key: str, value):
    global _cache
    await settings_col.update_one({"_id": "config"}, {"$set": {key: value}}, upsert=True)
    if _cache is not None:
        _cache[key] = value


async def get(key: str, default=None):
    settings = await get_settings()
    return settings.get(key, default)
