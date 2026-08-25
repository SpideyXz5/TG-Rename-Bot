from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import config


def main_settings_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Welcome Settings", callback_data="set:welcome")
    b.button(text="Bot Settings", callback_data="set:bot")
    b.button(text="Force Sub", callback_data="set:fsub")
    b.button(text="Shortener Settings", callback_data="set:shortener")
    b.button(text="Rename Settings", callback_data="set:rename")
    b.button(text="Metadata", callback_data="set:metadata")
    b.button(text="Bot Stats", callback_data="set:stats")
    b.button(text="Manage Admins", callback_data="set:admins")
    b.adjust(2)
    return b.as_markup()


def back_button(target: str = "set:main") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Back", callback_data=target)
    return b.as_markup()


def welcome_settings_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Set Welcome Photo", callback_data="welcome:photo")
    b.button(text="Set Welcome Message", callback_data="welcome:message")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def bot_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    maint = "ON" if settings.get("maintenance") else "OFF"
    pub = "ON" if settings.get("public_usage", True) else "OFF"
    b = InlineKeyboardBuilder()
    b.button(text=f"Maintenance: {maint}", callback_data="bot:maintenance")
    b.button(text=f"Public Usage: {pub}", callback_data="bot:public")
    b.button(text="Set Log Channel", callback_data="bot:logchannel")
    b.button(text="Set Dub Channel", callback_data="bot:dubchannel")
    b.button(text="Restart Bot", callback_data="bot:restart")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def force_sub_keyboard_admin(entries: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    used_slots = {e["slot"] for e in entries}
    for e in entries:
        state = "ON" if e.get("enabled") else "OFF"
        b.button(text=f"#{e['slot']} {e['type'].title()} [{state}]", callback_data=f"fsub:edit:{e['slot']}")
    if len(used_slots) < 6:
        b.button(text="+ Add Force Sub", callback_data="fsub:add")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def force_sub_entry_keyboard(slot: int, enabled: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Disable" if enabled else "Enable", callback_data=f"fsub:toggle:{slot}")
    b.button(text="Delete", callback_data=f"fsub:delete:{slot}")
    b.button(text="Back", callback_data="set:fsub")
    b.adjust(2, 1)
    return b.as_markup()


def force_sub_type_keyboard(slot: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Channel", callback_data=f"fsub:type:{slot}:channel")
    b.button(text="Group", callback_data=f"fsub:type:{slot}:group")
    b.button(text="Folder", callback_data=f"fsub:type:{slot}:folder")
    b.button(text="Cancel", callback_data="set:fsub")
    b.adjust(3, 1)
    return b.as_markup()


def shortener_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    state = "ON" if settings.get("shortener_enabled") else "OFF"
    b = InlineKeyboardBuilder()
    b.button(text="Set Domain", callback_data="short:domain")
    b.button(text="Set API", callback_data="short:api")
    b.button(text="Verification Duration", callback_data="short:duration")
    b.button(text=f"Shortener: {state}", callback_data="short:toggle")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def duration_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for label in config.VERIFY_DURATIONS:
        b.button(text=label, callback_data=f"short:setduration:{label}")
    b.button(text="Back", callback_data="set:shortener")
    b.adjust(3, 3, 1)
    return b.as_markup()


def rename_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    auto = "ON" if settings.get("auto_rename_enabled") else "OFF"
    anim = "ON" if settings.get("loading_animation", True) else "OFF"
    b = InlineKeyboardBuilder()
    b.button(text=f"Auto Rename: {auto}", callback_data="rename:autotoggle")
    b.button(text="Set Format", callback_data="rename:format")
    b.button(text="Set Caption", callback_data="rename:caption")
    b.button(text="Video Formats", callback_data="rename:videofmt")
    b.button(text="Document Formats", callback_data="rename:docfmt")
    b.button(text=f"Loading Animation: {anim}", callback_data="rename:animtoggle")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def output_format_keyboard(current: str, kind: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=("\u2713 " if current == "video" else "") + "Video", callback_data=f"outfmt:{kind}:video")
    b.button(text=("\u2713 " if current == "document" else "") + "Document", callback_data=f"outfmt:{kind}:document")
    if kind == "video":
        b.button(text=("\u2713 " if current == "audio" else "") + "Audio", callback_data=f"outfmt:{kind}:audio")
    b.button(text="Back", callback_data="set:rename")
    b.adjust(3, 1)
    return b.as_markup()


def metadata_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    state = "ON" if settings.get("metadata_enabled") else "OFF"
    b = InlineKeyboardBuilder()
    b.button(text=f"Metadata: {state}", callback_data="meta:toggle")
    b.button(text="Video Name", callback_data="meta:video")
    b.button(text="Audio Name", callback_data="meta:audio")
    b.button(text="Subtitle Name", callback_data="meta:subtitle")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def admin_settings_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Add Admin", callback_data="admin:add")
    b.button(text="Remove Admin", callback_data="admin:remove")
    b.button(text="View Admin List", callback_data="admin:list")
    b.button(text="Back", callback_data="set:main")
    b.adjust(1)
    return b.as_markup()


def cancel_input_keyboard(back_target: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Cancel", callback_data=back_target)
    return b.as_markup()
