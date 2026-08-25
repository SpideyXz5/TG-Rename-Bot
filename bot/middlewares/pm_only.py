from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class PMOnlyMiddleware(BaseMiddleware):
    """
    Blocks every update that isn't a private chat. Per spec this bot must
    never operate inside groups/channels — files are not processed there.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat = None
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        if chat is not None and chat.type != "private":
            if isinstance(event, Message):
                try:
                    await event.reply("<b>Please use this bot in PM.</b>")
                except Exception:
                    pass
            return  # swallow the update — do not process files/commands in groups

        return await handler(event, data)
