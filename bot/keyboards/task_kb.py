from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_task_keyboard(task_id: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Cancel Task", callback_data=f"canceltask:{task_id}")
    return b.as_markup()


def rename_mode_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Manual Rename", callback_data="mode:manual")
    b.button(text="Auto Rename", callback_data="mode:auto")
    b.adjust(2)
    return b.as_markup()
