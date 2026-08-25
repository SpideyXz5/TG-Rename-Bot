from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import config
from bot.database.settings import get_settings
from bot.database.admins import is_owner
from bot.handlers.start import gate_check
from bot.handlers.states import RenameStates
from bot.services.queue_manager import queue_manager, RenameTask
from bot.services.rename_parser import parse_filename
from bot.utils.filename_utils import build_output_filename
from bot.utils.formatting import apply_template, human_size, esc
from bot.database.thumbnails import get_thumbnail

router = Router(name="rename")


def _extract_file(message: Message):
    doc = message.document or message.video or message.audio
    if not doc:
        return None, None, 0
    return doc.file_id, getattr(doc, "file_name", None) or "file", getattr(doc, "file_size", 0) or 0


async def _enqueue_and_notify(message: Message, new_filename: str):
    thumb = get_thumbnail(message.from_user.id)
    task = RenameTask.new(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message=message,
        new_filename=new_filename,
        thumbnail_path=thumb,
    )
    position = await queue_manager.enqueue(task)

    if position is None:
        await message.reply("<b>Queue is full (20/20). Please try again later.</b>")
        return

    from bot.keyboards.task_kb import cancel_task_keyboard
    await message.reply(
        f"<b>Your task has been added to the queue.</b>\n<b>Position: {position}/{config.MAX_QUEUE_SIZE}</b>",
        reply_markup=cancel_task_keyboard(task.task_id),
    )


@router.message(F.document | F.video | F.audio, StateFilter(None))
async def on_file(message: Message, bot: Bot, state: FSMContext):
    file_id, file_name, file_size = _extract_file(message)
    if not file_id:
        return

    owner = is_owner(message.from_user.id)
    limit = config.OWNER_MAX_FILE_SIZE if owner else config.NORMAL_MAX_FILE_SIZE
    if file_size and file_size > limit:
        await message.reply(
            f"<b>File too large. Maximum allowed size is {esc(human_size(limit))}.</b>"
        )
        return

    if not await gate_check(bot, message):
        return

    settings = await get_settings()

    if settings.get("auto_rename_enabled"):
        parsed = parse_filename(file_name)
        raw_name = apply_template(settings.get("rename_format", "{title}"), **parsed)
        final_name = build_output_filename(raw_name, file_name)
        await _enqueue_and_notify(message, final_name)
        return

    await state.set_state(RenameStates.waiting_for_filename)
    await state.update_data(file_message=message)
    await message.reply("<b>Please send the new filename (extension optional).</b>")


@router.message(RenameStates.waiting_for_filename, F.text)
async def on_new_filename(message: Message, state: FSMContext):
    data = await state.get_data()
    file_message: Message = data.get("file_message")
    await state.clear()

    if file_message is None:
        await message.reply("<b>Session expired — please resend the file.</b>")
        return

    _, original_name, _ = _extract_file(file_message)
    final_name = build_output_filename(message.text, original_name)
    await _enqueue_and_notify(file_message, final_name)


@router.callback_query(F.data.startswith("canceltask:"))
async def cb_cancel_task(call: CallbackQuery):
    task_id = call.data.split(":", 1)[1]
    ok = await queue_manager.cancel(task_id)
    if ok:
        await call.answer("Task cancelled.")
        try:
            await call.message.edit_text("<b>Task cancelled.</b>")
        except Exception:
            pass
    else:
        await call.answer("Task already finished or not found.", show_alert=True)
