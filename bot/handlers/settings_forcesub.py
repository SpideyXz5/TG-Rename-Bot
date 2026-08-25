from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.filters.admin_filter import IsAdmin
from bot.database.force_subs import (
    get_all_force_subs, set_force_sub, toggle_force_sub, delete_force_sub, next_free_slot,
)
from bot.handlers.states import SettingsStates
from bot.keyboards.settings_kb import (
    force_sub_keyboard_admin, force_sub_entry_keyboard, force_sub_type_keyboard, cancel_input_keyboard,
)

router = Router(name="settings_forcesub")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "set:fsub")
async def cb_fsub_menu(call: CallbackQuery):
    entries = await get_all_force_subs()
    await call.message.edit_text(
        f"<b>Force Subscription ({len(entries)}/6)</b>",
        reply_markup=force_sub_keyboard_admin(entries),
    )
    await call.answer()


@router.callback_query(F.data == "fsub:add")
async def cb_fsub_add(call: CallbackQuery):
    slot = await next_free_slot()
    if slot is None:
        await call.answer("Maximum 6 force-sub entries reached.", show_alert=True)
        return
    await call.message.edit_text(f"<b>Select type for slot #{slot}:</b>", reply_markup=force_sub_type_keyboard(slot))
    await call.answer()


@router.callback_query(F.data.startswith("fsub:type:"))
async def cb_fsub_type(call: CallbackQuery, state: FSMContext):
    _, _, slot, sub_type = call.data.split(":")
    await state.set_state(SettingsStates.waiting_fsub_value)
    await state.update_data(fsub_slot=int(slot), fsub_type=sub_type)

    if sub_type == "folder":
        prompt = "<b>Send the folder invite link.</b>"
    else:
        prompt = f"<b>Forward a message from the {sub_type}, or send its Chat ID.</b>"

    await call.message.edit_text(prompt, reply_markup=cancel_input_keyboard("set:fsub"))
    await call.answer()


@router.message(SettingsStates.waiting_fsub_value)
async def on_fsub_value(message: Message, state: FSMContext):
    data = await state.get_data()
    slot = data["fsub_slot"]
    sub_type = data["fsub_type"]

    if sub_type == "folder":
        value = message.text.strip()
    else:
        value = message.forward_from_chat.id if message.forward_from_chat else message.text.strip()

    await set_force_sub(slot, sub_type, value, enabled=True)
    await state.clear()

    entries = await get_all_force_subs()
    await message.answer(f"<b>Force-sub slot #{slot} saved.</b>", reply_markup=force_sub_keyboard_admin(entries))


@router.callback_query(F.data.startswith("fsub:edit:"))
async def cb_fsub_edit(call: CallbackQuery):
    slot = int(call.data.split(":")[-1])
    entries = await get_all_force_subs()
    entry = next((e for e in entries if e["slot"] == slot), None)
    if not entry:
        await call.answer("Not found.", show_alert=True)
        return
    from bot.utils.formatting import esc
    text = (
        f"<b>Slot #{slot}</b>\n"
        f"<b>Type: {esc(entry['type'])}</b>\n"
        f"<b>Value: {esc(entry['value'])}</b>\n"
        f"<b>Status: {'ON' if entry['enabled'] else 'OFF'}</b>"
    )
    await call.message.edit_text(text, reply_markup=force_sub_entry_keyboard(slot, entry["enabled"]))
    await call.answer()


@router.callback_query(F.data.startswith("fsub:toggle:"))
async def cb_fsub_toggle(call: CallbackQuery):
    slot = int(call.data.split(":")[-1])
    entries = await get_all_force_subs()
    entry = next((e for e in entries if e["slot"] == slot), None)
    if not entry:
        await call.answer("Not found.", show_alert=True)
        return
    await toggle_force_sub(slot, not entry["enabled"])
    entries = await get_all_force_subs()
    await call.message.edit_text(f"<b>Force Subscription ({len(entries)}/6)</b>", reply_markup=force_sub_keyboard_admin(entries))
    await call.answer()


@router.callback_query(F.data.startswith("fsub:delete:"))
async def cb_fsub_delete(call: CallbackQuery):
    slot = int(call.data.split(":")[-1])
    await delete_force_sub(slot)
    entries = await get_all_force_subs()
    await call.message.edit_text(f"<b>Force Subscription ({len(entries)}/6)</b>", reply_markup=force_sub_keyboard_admin(entries))
    await call.answer("Deleted.")
