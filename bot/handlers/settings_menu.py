from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.filters.admin_filter import IsAdmin, IsOwner
from bot.database.settings import get_settings, set_setting
from bot.database.admins import is_owner
from bot.handlers.states import SettingsStates
from bot.keyboards.settings_kb import (
    main_settings_keyboard, welcome_settings_keyboard, bot_settings_keyboard,
    cancel_input_keyboard,
)
from bot.services.queue_manager import queue_manager

router = Router(name="settings_menu")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ---------- Entry point ----------

@router.message(Command("settings"))
async def cmd_settings(message: Message):
    await message.answer("<b>Settings</b>", reply_markup=main_settings_keyboard())


@router.callback_query(F.data == "set:main")
async def cb_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("<b>Settings</b>", reply_markup=main_settings_keyboard())
    await call.answer()


# ---------- Welcome Settings ----------

@router.callback_query(F.data == "set:welcome")
async def cb_welcome(call: CallbackQuery):
    await call.message.edit_text("<b>Welcome Settings</b>", reply_markup=welcome_settings_keyboard())
    await call.answer()


@router.callback_query(F.data == "welcome:photo")
async def cb_welcome_photo(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_welcome_photo)
    await call.message.edit_text("<b>Send the new welcome photo.</b>", reply_markup=cancel_input_keyboard("set:welcome"))
    await call.answer()


@router.message(SettingsStates.waiting_welcome_photo, F.photo)
async def on_welcome_photo(message: Message, state: FSMContext):
    await set_setting("welcome_photo", message.photo[-1].file_id)
    await state.clear()
    await message.answer("<b>Welcome photo updated.</b>", reply_markup=welcome_settings_keyboard())


@router.callback_query(F.data == "welcome:message")
async def cb_welcome_message(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_welcome_message)
    await call.message.edit_text(
        "<b>Send the new welcome message.</b>\n\n"
        "<b>Supported variables: {mention} {first_name} {last_name} {username} {id}</b>\n"
        "<b>HTML formatting is supported.</b>",
        reply_markup=cancel_input_keyboard("set:welcome"),
    )
    await call.answer()


@router.message(SettingsStates.waiting_welcome_message, F.text)
async def on_welcome_message(message: Message, state: FSMContext):
    await set_setting("welcome_message", message.html_text)
    await state.clear()
    await message.answer("<b>Welcome message updated.</b>", reply_markup=welcome_settings_keyboard())


# ---------- Bot Settings ----------

@router.callback_query(F.data == "set:bot")
async def cb_bot(call: CallbackQuery):
    settings = await get_settings()
    await call.message.edit_text("<b>Bot Settings</b>", reply_markup=bot_settings_keyboard(settings))
    await call.answer()


@router.callback_query(F.data == "bot:maintenance")
async def cb_maintenance_toggle(call: CallbackQuery):
    settings = await get_settings()
    new_val = not settings.get("maintenance", False)
    await set_setting("maintenance", new_val)
    settings = await get_settings()
    await call.message.edit_text("<b>Bot Settings</b>", reply_markup=bot_settings_keyboard(settings))
    await call.answer(f"Maintenance {'ON' if new_val else 'OFF'}")


@router.callback_query(F.data == "bot:public")
async def cb_public_toggle(call: CallbackQuery):
    settings = await get_settings()
    new_val = not settings.get("public_usage", True)
    await set_setting("public_usage", new_val)
    settings = await get_settings()
    await call.message.edit_text("<b>Bot Settings</b>", reply_markup=bot_settings_keyboard(settings))
    await call.answer(f"Public Usage {'ON' if new_val else 'OFF'}")


@router.callback_query(F.data == "bot:logchannel")
async def cb_log_channel(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_log_channel)
    await call.message.edit_text(
        "<b>Forward a message from the log channel, or send its Chat ID.</b>",
        reply_markup=cancel_input_keyboard("set:bot"),
    )
    await call.answer()


@router.message(SettingsStates.waiting_log_channel)
async def on_log_channel(message: Message, state: FSMContext):
    chat_id = message.forward_from_chat.id if message.forward_from_chat else message.text.strip()
    await set_setting("log_channel", chat_id)
    await state.clear()
    settings = await get_settings()
    await message.answer("<b>Log channel set.</b>", reply_markup=bot_settings_keyboard(settings))


@router.callback_query(F.data == "bot:dubchannel")
async def cb_dub_channel(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_dub_channel)
    await call.message.edit_text(
        "<b>Forward a message from the dub channel, or send its Chat ID.</b>",
        reply_markup=cancel_input_keyboard("set:bot"),
    )
    await call.answer()


@router.message(SettingsStates.waiting_dub_channel)
async def on_dub_channel(message: Message, state: FSMContext):
    chat_id = message.forward_from_chat.id if message.forward_from_chat else message.text.strip()
    await set_setting("dub_channel", chat_id)
    await state.clear()
    settings = await get_settings()
    await message.answer("<b>Dub channel set.</b>", reply_markup=bot_settings_keyboard(settings))


@router.callback_query(F.data == "bot:restart")
async def cb_restart(call: CallbackQuery, bot: Bot):
    if not is_owner(call.from_user.id):
        await call.answer("Owner only.", show_alert=True)
        return
    await queue_manager.cancel_all()
    await call.answer("Restarting... all running/waiting tasks cancelled.", show_alert=True)
    import os, sys
    os.execv(sys.executable, [sys.executable] + sys.argv)
