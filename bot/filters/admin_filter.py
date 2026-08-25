from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from bot.database.admins import is_admin, is_owner


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        user = event.from_user
        if user is None:
            return False
        return await is_admin(user.id)


class IsOwner(BaseFilter):
    async def __call__(self, event) -> bool:
        user = event.from_user
        if user is None:
            return False
        return is_owner(user.id)
