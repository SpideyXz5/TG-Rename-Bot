from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.database.settings import get_settings
from bot.database.admins import is_admin


class MaintenanceMiddleware(BaseMiddleware):
    """
    When maintenance mode is ON, only admins/owner may use the bot.
    When public_usage is OFF, only known users who were previously granted
    access (admins) may use it — same enforcement point.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is None:
            return await handler(event, data)

        settings = await get_settings()
        admin = await is_admin(user.id)

        if settings.get("maintenance") and not admin:
            text = "<b>Bot is currently under maintenance. Please try again later.</b>"
            if isinstance(event, Message):
                await event.reply(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("Bot is currently under maintenance. Please try again later.", show_alert=True)
            return

        if not settings.get("public_usage", True) and not admin:
            text = "<b>This bot is currently restricted to admins only.</b>"
            if isinstance(event, Message):
                await event.reply(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("This bot is currently restricted to admins only.", show_alert=True)
            return

        return await handler(event, data)
