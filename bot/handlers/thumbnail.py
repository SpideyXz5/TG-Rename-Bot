import os

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.database.thumbnails import set_thumbnail, get_thumbnail, delete_thumbnail, thumb_path_for
from bot.keyboards.start_kb import thumbnail_keyboard

router = Router(name="thumbnail")


@router.message(F.photo, StateFilter(None))
async def on_photo(message: Message, bot: Bot):
    """Any image sent in PM (outside of an active settings flow) becomes the user's thumbnail."""
    user_id = message.from_user.id
    dest = thumb_path_for(user_id)
    await bot.download(message.photo[-1].file_id, destination=dest)
    set_thumbnail(user_id, dest)
    await message.reply("<b>Thumbnail set successfully.</b>", reply_markup=thumbnail_keyboard())


@router.callback_query(F.data == "thumb_view")
async def cb_view(call: CallbackQuery):
    path = get_thumbnail(call.from_user.id)
    if not path:
        await call.answer("No thumbnail set.", show_alert=True)
        return
    await call.message.answer_photo(FSInputFile(path))
    await call.answer()


@router.callback_query(F.data == "thumb_change")
async def cb_change(call: CallbackQuery):
    await call.message.answer("<b>Send a new photo to replace your thumbnail.</b>")
    await call.answer()


@router.callback_query(F.data == "thumb_delete")
async def cb_delete(call: CallbackQuery):
    delete_thumbnail(call.from_user.id)
    await call.answer("Thumbnail deleted.", show_alert=True)
    try:
        await call.message.delete()
    except Exception:
        pass
