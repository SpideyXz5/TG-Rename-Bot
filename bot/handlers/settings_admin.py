from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.filters.admin_filter import IsAdmin, IsOwner
from bot.database.admins import add_admin, remove_admin, list_admins, is_owner
from bot.handlers.states import SettingsStates
from bot.keyboards.settings_kb import admin_settings_keyboard, cancel_input_keyboard
from bot.config import config

router = Router(name="settings_admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "set:admins")
async def cb_menu(call: CallbackQuery):
    await call.message.edit_text("<b>Manage Admins</b>", reply_markup=admin_settings_keyboard())
    await call.answer()


@router.callback_query(F.data == "admin:add")
async def cb_add(call: CallbackQuery, state: FSMContext):
    if not is_owner(call.from_user.id):
        await call.answer("Owner only.", show_alert=True)
        return
    await state.set_state(SettingsStates.waiting_admin_add)
    await call.message.edit_text("<b>Send the User ID to add as admin.</b>", reply_markup=cancel_input_keyboard("set:admins"))
    await call.answer()


@router.message(SettingsStates.waiting_admin_add, F.text)
async def on_add(message: Message, state: FSMContext):
    await state.clear()
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("<b>Invalid User ID.</b>", reply_markup=admin_settings_keyboard())
        return
    added = await add_admin(user_id, message.from_user.id)
    text = f"<b>Added {user_id} as admin.</b>" if added else f"<b>{user_id} is already an admin.</b>"
    await message.answer(text, reply_markup=admin_settings_keyboard())


@router.callback_query(F.data == "admin:remove")
async def cb_remove(call: CallbackQuery, state: FSMContext):
    if not is_owner(call.from_user.id):
        await call.answer("Owner only.", show_alert=True)
        return
    await state.set_state(SettingsStates.waiting_admin_remove)
    await call.message.edit_text("<b>Send the User ID to remove.</b>", reply_markup=cancel_input_keyboard("set:admins"))
    await call.answer()


@router.message(SettingsStates.waiting_admin_remove, F.text)
async def on_remove(message: Message, state: FSMContext):
    await state.clear()
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("<b>Invalid User ID.</b>", reply_markup=admin_settings_keyboard())
        return
    removed = await remove_admin(user_id)
    text = f"<b>Removed {user_id} from admins.</b>" if removed else f"<b>{user_id} was not an admin.</b>"
    await message.answer(text, reply_markup=admin_settings_keyboard())


@router.callback_query(F.data == "admin:list")
async def cb_list(call: CallbackQuery):
    admins = await list_admins()
    lines = [f"<b>Owner: {config.OWNER_ID}</b>"] + [f"<b>Admin: {a}</b>" for a in admins]
    await call.message.edit_text("\n".join(lines) or "<b>No admins yet.</b>", reply_markup=admin_settings_keyboard())
    await call.answer()
