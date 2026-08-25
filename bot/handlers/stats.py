from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.filters.admin_filter import IsAdmin
from bot.database.tasks import get_stats
from bot.database.users import total_users
from bot.services.queue_manager import queue_manager
from bot.keyboards.settings_kb import back_button
from bot.utils.formatting import human_size, esc

router = Router(name="stats")
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "set:stats")
async def cb_stats(call: CallbackQuery):
    stats = await get_stats()
    users = await total_users()
    q = queue_manager.stats()

    text = (
        "<b>Bot Stats (All-Time)</b>\n\n"
        f"<b>Total Users: {users}</b>\n"
        f"<b>Total Rename Tasks: {stats['total_renames']}</b>\n"
        f"<b>Successful Renames: {stats['successful_renames']}</b>\n"
        f"<b>Failed Renames: {stats['failed_renames']}</b>\n"
        f"<b>Cancelled Tasks: {stats['cancelled_tasks']}</b>\n"
        f"<b>Total Files Processed: {stats['total_files_processed']}</b>\n"
        f"<b>Total Processing Size: {esc(human_size(stats['total_processing_size']))}</b>\n\n"
        f"<b>Current Running Task: {q['running']}</b>\n"
        f"<b>Waiting Queue Count: {q['waiting']}</b>"
    )
    await call.message.edit_text(text, reply_markup=back_button())
    await call.answer()
