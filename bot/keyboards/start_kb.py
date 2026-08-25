from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def welcome_keyboard(update_url: str = None, support_url: str = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if update_url:
        b.button(text="Update", url=update_url)
    if support_url:
        b.button(text="Support", url=support_url)
    b.button(text="Help", callback_data="help")
    b.adjust(2, 1)
    return b.as_markup()


def force_sub_keyboard(missing_entries: list) -> InlineKeyboardMarkup:
    from bot.services.force_sub import build_join_url

    b = InlineKeyboardBuilder()
    for i, entry in enumerate(missing_entries, start=1):
        b.button(text=f"Join {i}", url=build_join_url(entry))
    b.button(text="Joined \u2713 Check Again", callback_data="fsub_check")
    b.adjust(2)
    return b.as_markup()


def shortener_keyboard(short_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Verify", url=short_url)
    b.button(text="I've Verified \u2713", callback_data="verify_check")
    b.adjust(1)
    return b.as_markup()


def thumbnail_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="View Thumbnail", callback_data="thumb_view")
    b.button(text="Change Thumbnail", callback_data="thumb_change")
    b.button(text="Delete Thumbnail", callback_data="thumb_delete")
    b.adjust(2, 1)
    return b.as_markup()
