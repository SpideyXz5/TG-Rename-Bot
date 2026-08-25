from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.filters.admin_filter import IsAdmin
from bot.database.settings import get_settings, set_setting
from bot.handlers.states import SettingsStates
from bot.keyboards.settings_kb import (
    rename_settings_keyboard, output_format_keyboard, metadata_settings_keyboard, cancel_input_keyboard,
)

router = Router(name="settings_rename")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ---------- Rename Settings ----------

@router.callback_query(F.data == "set:rename")
async def cb_menu(call: CallbackQuery):
    settings = await get_settings()
    await call.message.edit_text("<b>Rename Settings</b>", reply_markup=rename_settings_keyboard(settings))
    await call.answer()


@router.callback_query(F.data == "rename:autotoggle")
async def cb_auto_toggle(call: CallbackQuery):
    settings = await get_settings()
    new_val = not settings.get("auto_rename_enabled", False)
    await set_setting("auto_rename_enabled", new_val)
    settings = await get_settings()
    await call.message.edit_text("<b>Rename Settings</b>", reply_markup=rename_settings_keyboard(settings))
    await call.answer(f"Auto Rename {'ON' if new_val else 'OFF'}")


@router.callback_query(F.data == "rename:animtoggle")
async def cb_anim_toggle(call: CallbackQuery):
    settings = await get_settings()
    new_val = not settings.get("loading_animation", True)
    await set_setting("loading_animation", new_val)
    settings = await get_settings()
    await call.message.edit_text("<b>Rename Settings</b>", reply_markup=rename_settings_keyboard(settings))
    await call.answer(f"Loading Animation {'ON' if new_val else 'OFF'}")


@router.callback_query(F.data == "rename:format")
async def cb_format(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_rename_format)
    await call.message.edit_text(
        "<b>Send the auto-rename format.</b>\n\n"
        "<b>Variables: {title} {season} {episode} {quality} {audio}</b>\n\n"
        "<b>Example: {title} S{season} E{episode} [{quality}] {audio}</b>",
        reply_markup=cancel_input_keyboard("set:rename"),
    )
    await call.answer()


@router.message(SettingsStates.waiting_rename_format, F.text)
async def on_format(message: Message, state: FSMContext):
    await set_setting("rename_format", message.text)
    await state.clear()
    settings = await get_settings()
    await message.answer("<b>Rename format saved.</b>", reply_markup=rename_settings_keyboard(settings))


@router.callback_query(F.data == "rename:caption")
async def cb_caption(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_caption)
    await call.message.edit_text(
        "<b>Send the caption template (HTML supported).</b>\n\n"
        "<b>Variables: {filename} {filesize} {user} {id} {title} {season} {episode} {quality} {audio}</b>",
        reply_markup=cancel_input_keyboard("set:rename"),
    )
    await call.answer()


@router.message(SettingsStates.waiting_caption, F.text)
async def on_caption(message: Message, state: FSMContext):
    await set_setting("caption", message.html_text)
    await state.clear()
    settings = await get_settings()
    await message.answer("<b>Caption saved.</b>", reply_markup=rename_settings_keyboard(settings))


@router.callback_query(F.data == "rename:videofmt")
async def cb_video_fmt(call: CallbackQuery):
    settings = await get_settings()
    await call.message.edit_text(
        "<b>Select output method for videos:</b>",
        reply_markup=output_format_keyboard(settings.get("video_format", "video"), "video"),
    )
    await call.answer()


@router.callback_query(F.data == "rename:docfmt")
async def cb_doc_fmt(call: CallbackQuery):
    settings = await get_settings()
    await call.message.edit_text(
        "<b>Select output method for documents:</b>",
        reply_markup=output_format_keyboard(settings.get("document_format", "document"), "document"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("outfmt:"))
async def cb_set_outfmt(call: CallbackQuery):
    _, kind, value = call.data.split(":")
    key = "video_format" if kind == "video" else "document_format"
    await set_setting(key, value)
    settings = await get_settings()
    await call.message.edit_text("<b>Rename Settings</b>", reply_markup=rename_settings_keyboard(settings))
    await call.answer("Saved.")


# ---------- Metadata Settings ----------

@router.callback_query(F.data == "set:metadata")
async def cb_meta_menu(call: CallbackQuery):
    settings = await get_settings()
    await call.message.edit_text("<b>Metadata Settings</b>", reply_markup=metadata_settings_keyboard(settings))
    await call.answer()


@router.callback_query(F.data == "meta:toggle")
async def cb_meta_toggle(call: CallbackQuery):
    settings = await get_settings()
    new_val = not settings.get("metadata_enabled", False)
    await set_setting("metadata_enabled", new_val)
    settings = await get_settings()
    await call.message.edit_text("<b>Metadata Settings</b>", reply_markup=metadata_settings_keyboard(settings))
    await call.answer(f"Metadata {'ON' if new_val else 'OFF'}")


_META_FIELD_STATE = {
    "video": (SettingsStates.waiting_metadata_video, "metadata_video"),
    "audio": (SettingsStates.waiting_metadata_audio, "metadata_audio"),
    "subtitle": (SettingsStates.waiting_metadata_subtitle, "metadata_subtitle"),
}


@router.callback_query(F.data.in_({"meta:video", "meta:audio", "meta:subtitle"}))
async def cb_meta_field(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[-1]
    target_state, _ = _META_FIELD_STATE[kind]
    await state.set_state(target_state)
    await state.update_data(meta_kind=kind)
    await call.message.edit_text(f"<b>Send the {kind} track name.</b>", reply_markup=cancel_input_keyboard("set:metadata"))
    await call.answer()


@router.message(SettingsStates.waiting_metadata_video, F.text)
@router.message(SettingsStates.waiting_metadata_audio, F.text)
@router.message(SettingsStates.waiting_metadata_subtitle, F.text)
async def on_meta_field(message: Message, state: FSMContext):
    data = await state.get_data()
    kind = data.get("meta_kind")
    _, key = _META_FIELD_STATE[kind]
    await set_setting(key, message.text)
    await state.clear()
    settings = await get_settings()
    await message.answer(f"<b>{kind.title()} name saved.</b>", reply_markup=metadata_settings_keyboard(settings))
