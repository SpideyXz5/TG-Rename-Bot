from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.filters.admin_filter import IsAdmin
from bot.config import config
from bot.database.settings import get_settings, set_setting
from bot.handlers.states import SettingsStates
from bot.keyboards.settings_kb import shortener_settings_keyboard, duration_keyboard, cancel_input_keyboard

router = Router(name="settings_shortener")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "set:shortener")
async def cb_menu(call: CallbackQuery):
    settings = await get_settings()
    await call.message.edit_text("<b>Shortener Settings</b>", reply_markup=shortener_settings_keyboard(settings))
    await call.answer()


@router.callback_query(F.data == "short:toggle")
async def cb_toggle(call: CallbackQuery):
    settings = await get_settings()
    new_val = not settings.get("shortener_enabled", False)
    await set_setting("shortener_enabled", new_val)
    settings = await get_settings()
    await call.message.edit_text("<b>Shortener Settings</b>", reply_markup=shortener_settings_keyboard(settings))
    await call.answer(f"Shortener {'ON' if new_val else 'OFF'}")


@router.callback_query(F.data == "short:domain")
async def cb_domain(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_shortener_domain)
    await call.message.edit_text("<b>Send the shortener domain (e.g. vplink.in).</b>", reply_markup=cancel_input_keyboard("set:shortener"))
    await call.answer()


@router.message(SettingsStates.waiting_shortener_domain, F.text)
async def on_domain(message: Message, state: FSMContext):
    await set_setting("shortener_domain", message.text.strip())
    await state.clear()
    settings = await get_settings()
    await message.answer("<b>Domain saved.</b>", reply_markup=shortener_settings_keyboard(settings))


@router.callback_query(F.data == "short:api")
async def cb_api(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_shortener_api)
    await call.message.edit_text("<b>Send the shortener API key.</b>", reply_markup=cancel_input_keyboard("set:shortener"))
    await call.answer()


@router.message(SettingsStates.waiting_shortener_api, F.text)
async def on_api(message: Message, state: FSMContext):
    await set_setting("shortener_api", message.text.strip())
    await state.clear()
    settings = await get_settings()
    await message.answer("<b>API key saved.</b>", reply_markup=shortener_settings_keyboard(settings))
    try:
        await message.delete()  # keep the API key out of chat history
    except Exception:
        pass


@router.callback_query(F.data == "short:duration")
async def cb_duration_menu(call: CallbackQuery):
    await call.message.edit_text("<b>Select verification duration:</b>", reply_markup=duration_keyboard())
    await call.answer()


@router.callback_query(F.data.startswith("short:setduration:"))
async def cb_set_duration(call: CallbackQuery):
    label = call.data.split(":")[-1]
    seconds = config.VERIFY_DURATIONS.get(label)
    if seconds is None:
        await call.answer("Invalid duration.", show_alert=True)
        return
    await set_setting("shortener_duration", seconds)
    settings = await get_settings()
    await call.message.edit_text("<b>Shortener Settings</b>", reply_markup=shortener_settings_keyboard(settings))
    await call.answer(f"Duration set to {label}")
