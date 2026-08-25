import time
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

from bot.utils.formatting import progress_bar, human_size
from bot.config import config
from bot.keyboards.task_kb import cancel_task_keyboard


class ProgressReporter:
    """
    Wraps the "editMessageText" calls needed to show a live progress bar,
    throttled to config.PROGRESS_EDIT_INTERVAL seconds so we never trip
    Telegram's flood limits, even on fast local uploads/downloads.
    """

    def __init__(self, bot: Bot, chat_id: int, message_id: int, task_id: str):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.task_id = task_id
        self._last_edit = 0.0
        self._last_text = None

    async def update(self, stage: str, done: int = 0, total: int = 0, extra: str = ""):
        percent = (done / total * 100) if total else 0
        now = time.time()
        if now - self._last_edit < config.PROGRESS_EDIT_INTERVAL and percent < 100:
            return

        bar = progress_bar(percent)
        text = f"<b>{stage}</b>\n<b>{bar} {percent:.0f}%</b>"
        if total:
            text += f"\n<b>{human_size(done)} / {human_size(total)}</b>"
        if extra:
            text += f"\n<b>{extra}</b>"

        if text == self._last_text:
            return

        try:
            await self.bot.edit_message_text(
                text,
                chat_id=self.chat_id,
                message_id=self.message_id,
                reply_markup=cancel_task_keyboard(self.task_id),
            )
            self._last_edit = now
            self._last_text = text
        except TelegramRetryAfter as e:
            self._last_edit = now + e.retry_after
        except TelegramBadRequest:
            pass  # message unchanged / deleted — non-fatal

    async def set_stage(self, stage: str):
        await self._force_update(f"<b>{stage}</b>...")

    async def _force_update(self, text: str):
        try:
            await self.bot.edit_message_text(
                text,
                chat_id=self.chat_id,
                message_id=self.message_id,
                reply_markup=cancel_task_keyboard(self.task_id),
            )
            self._last_text = text
            self._last_edit = time.time()
        except (TelegramBadRequest, TelegramRetryAfter):
            pass
