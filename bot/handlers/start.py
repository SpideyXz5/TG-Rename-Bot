from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery

from bot.database.users import add_user
from bot.database.settings import get_settings
from bot.database.verification import is_verified, set_verified
from bot.services.force_sub import get_missing_force_subs
from bot.keyboards.start_kb import welcome_keyboard, force_sub_keyboard, shortener_keyboard
from bot.services.shortener_api import shorten_url
from bot.utils.formatting import apply_template, esc
from bot.config import config

router = Router(name="start")


def _fill_welcome_vars(template: str, user) -> str:
    first_name = esc(user.first_name or "")
    return apply_template(
        template,
        mention=f'<a href="tg://user?id={user.id}">{first_name}</a>',
        first_name=first_name,
        last_name=esc(user.last_name or ""),
        username=f"@{esc(user.username)}" if user.username else "",
        id=user.id,
    )


async def gate_check(bot: Bot, message: Message) -> bool:
    """
    Runs the Force-Sub -> Shortener gate. Returns True if the user is clear
    to proceed (used both on /start and before accepting a file).
    """
    user = message.from_user
    missing = await get_missing_force_subs(bot, user.id)
    if missing:
        await message.answer(
            "<b>You must join the following to use this bot:</b>",
            reply_markup=force_sub_keyboard(missing),
        )
        return False

    settings = await get_settings()
    if settings.get("shortener_enabled"):
        if not await is_verified(user.id):
            bot_username = (await bot.get_me()).username
            deep_link = f"https://t.me/{bot_username}?start=verify_{user.id}"
            short = await shorten_url(settings.get("shortener_domain"), settings.get("shortener_api"), deep_link)
            link_to_send = short or deep_link
            await message.answer(
                "<b>Please complete verification to continue using the bot:</b>",
                reply_markup=shortener_keyboard(link_to_send),
            )
            return False

    return True


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, command: CommandObject):
    user = message.from_user
    await add_user(user.id, user.first_name or "", user.username or "")

    # Shortener redirects the user back here as /start verify_<user_id>
    if command.args and command.args.startswith("verify_"):
        settings = await get_settings()
        duration = settings.get("shortener_duration", 3 * 60 * 60)
        await set_verified(user.id, duration)
        await message.answer("<b>Verification successful! You can now send files.</b>")
        return

    settings = await get_settings()
    # Admin-configured content — preserve their own HTML formatting as-is.
    text = _fill_welcome_vars(settings.get("welcome_message", ""), user)
    photo = settings.get("welcome_photo")

    kb = welcome_keyboard(support_url=None, update_url=None)

    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Send me a file and I'll rename it for you.</b>\n\n"
        "<b>Send a photo to set it as your rename thumbnail.</b>\n\n"
        f"<b>Developer: {config.DEVELOPER_CREDIT}</b>"
    )


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.message.answer(
        "<b>Send me a file and I'll rename it for you.</b>\n\n"
        "<b>Send a photo to set it as your rename thumbnail.</b>\n\n"
        f"<b>Developer: {config.DEVELOPER_CREDIT}</b>"
    )
    await call.answer()


@router.callback_query(F.data == "fsub_check")
async def cb_fsub_check(call: CallbackQuery, bot: Bot):
    missing = await get_missing_force_subs(bot, call.from_user.id)
    if missing:
        await call.answer("You haven't joined everything yet.", show_alert=True)
        return
    await call.message.edit_text("<b>Thanks! You can now use the bot. Send /start again or send a file.</b>")
    await call.answer()


@router.callback_query(F.data == "verify_check")
async def cb_verify_check(call: CallbackQuery):
    if await is_verified(call.from_user.id):
        await call.message.edit_text("<b>Verification confirmed. You can now send files.</b>")
    else:
        await call.answer("Verification not detected yet. Please complete it first.", show_alert=True)
    await call.answer()
