from aiogram.fsm.state import StatesGroup, State


class RenameStates(StatesGroup):
    waiting_for_filename = State()


class SettingsStates(StatesGroup):
    waiting_welcome_photo = State()
    waiting_welcome_message = State()

    waiting_log_channel = State()
    waiting_dub_channel = State()

    waiting_fsub_value = State()

    waiting_shortener_domain = State()
    waiting_shortener_api = State()

    waiting_rename_format = State()
    waiting_caption = State()

    waiting_metadata_video = State()
    waiting_metadata_audio = State()
    waiting_metadata_subtitle = State()

    waiting_admin_add = State()
    waiting_admin_remove = State()
