from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from bot.database.force_subs import get_enabled_force_subs


async def get_missing_force_subs(bot: Bot, user_id: int):
    """
    Returns a list of force-sub entries the user has NOT satisfied yet.
    Empty list = user satisfies every enabled requirement.
    """
    missing = []
    entries = await get_enabled_force_subs()

    for entry in entries:
        sub_type = entry["type"]

        if sub_type in ("channel", "group"):
            try:
                member = await bot.get_chat_member(chat_id=entry["value"], user_id=user_id)
                if member.status in ("left", "kicked"):
                    missing.append(entry)
            except TelegramBadRequest:
                # bot isn't admin there / chat not found — treat as unmet so admin notices
                missing.append(entry)
        elif sub_type == "folder":
            # Folder links can't be verified via Bot API membership calls —
            # we can only prompt the user to join; assume unmet until they've
            # pressed "Joined \u2713 Check Again" at least once per session.
            missing.append(entry)

    return missing


def build_join_url(entry: dict) -> str:
    value = entry["value"]
    if isinstance(value, str) and value.startswith("http"):
        return value
    return f"https://t.me/{str(value).lstrip('@')}"
