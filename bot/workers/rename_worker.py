"""
Executed one-at-a-time by QueueManager.run_forever(). Handles the full
lifecycle of a single rename task: download -> rename -> metadata ->
upload -> dub channel -> log channel -> stats, with cancel checks at
every stage and automatic retry on transient failures.
"""
import asyncio
import os
import time

import aiohttp
from aiogram import Bot
from aiogram.types import FSInputFile, InputFile
from aiogram.exceptions import TelegramBadRequest

from bot.config import config
from bot.database import tasks as tasks_db
from bot.database.settings import get_settings
from bot.services.progress import ProgressReporter
from bot.services.queue_manager import RenameTask, TaskCancelled
from bot.services.metadata import apply_metadata, is_media_container
from bot.utils.formatting import human_size, apply_template, esc
from bot.utils.logger import logger

FIXED_ERRORS = {
    "download": "<b>Download failed. Please try again.</b>",
    "upload": "<b>Upload failed. Please try again.</b>",
    "rename": "<b>Rename failed due to an internal error.</b>",
    "metadata": "<b>Metadata processing failed — file was still delivered without it.</b>",
    "cancelled": "<b>Task cancelled.</b>",
    "generic": "<b>Something went wrong while processing your file.</b>",
}


class ProgressFSInputFile(FSInputFile):
    """FSInputFile subclass that reports read progress and honours cancellation."""

    def __init__(self, path, filename, reporter: ProgressReporter, total: int, cancel_event: asyncio.Event):
        super().__init__(path, filename=filename)
        self._reporter = reporter
        self._total = total
        self._sent = 0
        self._cancel_event = cancel_event

    async def read(self, chunk_size: int):
        async for chunk in super().read(chunk_size):
            if self._cancel_event.is_set():
                raise TaskCancelled()
            self._sent += len(chunk)
            await self._reporter.update("Uploading", self._sent, self._total)
            yield chunk


async def _download_with_progress(bot: Bot, file_id: str, dest_path: str, reporter: ProgressReporter, cancel_event: asyncio.Event):
    tg_file = await bot.get_file(file_id)
    total = tg_file.file_size or 0
    url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{tg_file.file_path}"

    downloaded = 0
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            with open(dest_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 256):
                    if cancel_event.is_set():
                        raise TaskCancelled()
                    f.write(chunk)
                    downloaded += len(chunk)
                    await reporter.update("Downloading", downloaded, total)
    return total


def _extract_file_info(message):
    doc = message.document or message.video or message.audio
    file_id = doc.file_id
    file_name = getattr(doc, "file_name", None) or "file"
    file_size = getattr(doc, "file_size", 0) or 0
    return file_id, file_name, file_size


async def _send_to_log_channel(bot: Bot, log_channel, user, filename: str, filesize: int, status: str):
    if not log_channel:
        return
    text = (
        f"<b>User:</b> <b>{esc(user.first_name)}</b>\n"
        f"<b>User ID:</b> <b>{user.id}</b>\n"
        f"<b>Rename File:</b> <b>{esc(filename)}</b>\n"
        f"<b>File Size:</b> <b>{esc(human_size(filesize))}</b>\n"
        f"<b>Status:</b> <b>{status}</b>"
    )
    try:
        await bot.send_message(log_channel, text)
    except Exception as e:
        logger.warning(f"Log channel send failed: {e}")


async def _send_to_dub_channel(bot: Bot, dub_channel, output_path: str, filename: str, output_kind: str, thumb, caption: str):
    if not dub_channel:
        return
    try:
        file_input = FSInputFile(output_path, filename=filename)
        if output_kind == "video":
            await bot.send_video(dub_channel, file_input, caption=caption, thumbnail=thumb)
        elif output_kind == "audio":
            await bot.send_audio(dub_channel, file_input, caption=caption, thumbnail=thumb)
        else:
            await bot.send_document(dub_channel, file_input, caption=caption, thumbnail=thumb)
    except Exception as e:
        logger.warning(f"Dub channel upload failed (user's copy was not affected): {e}")


async def process_task(task: RenameTask, bot: Bot):
    settings = await get_settings()
    user = task.message.from_user
    file_id, original_name, file_size = _extract_file_info(task.message)

    status_msg = await bot.send_message(task.chat_id, "<b>Starting task...</b>")
    task.status_message_id = status_msg.message_id
    reporter = ProgressReporter(bot, task.chat_id, status_msg.message_id, task.task_id)

    await tasks_db.create_task_record(task.task_id, task.user_id, task.new_filename, file_size)

    work_dir = os.path.join(config.DOWNLOAD_DIR, task.task_id)
    os.makedirs(work_dir, exist_ok=True)
    raw_path = os.path.join(work_dir, f"raw_{original_name}")
    final_path = os.path.join(work_dir, task.new_filename)
    metadata_path = os.path.join(work_dir, f"meta_{task.new_filename}")

    attempt = 0
    success = False
    last_error = None

    try:
        while attempt < config.MAX_RETRIES and not success:
            attempt += 1
            try:
                if task.cancel_event.is_set():
                    raise TaskCancelled()

                # --- Download ---
                await reporter.set_stage("Downloading")
                await _download_with_progress(bot, file_id, raw_path, reporter, task.cancel_event)

                if task.cancel_event.is_set():
                    raise TaskCancelled()

                # --- Rename (local move) ---
                await reporter.set_stage("Renaming")
                os.replace(raw_path, final_path)

                if task.cancel_event.is_set():
                    raise TaskCancelled()

                # --- Metadata (optional, MKV/MP4 only) ---
                upload_path = final_path
                if settings.get("metadata_enabled") and is_media_container(final_path):
                    await reporter.set_stage("Metadata")
                    ok = await apply_metadata(
                        final_path, metadata_path,
                        settings.get("metadata_video", ""),
                        settings.get("metadata_audio", ""),
                        settings.get("metadata_subtitle", ""),
                    )
                    if ok:
                        upload_path = metadata_path

                if task.cancel_event.is_set():
                    raise TaskCancelled()

                # --- Upload ---
                output_kind = settings.get("video_format", "video") if task.message.video else settings.get("document_format", "document")

                from bot.database.thumbnails import get_thumbnail
                thumb_path = task.thumbnail_path or get_thumbnail(task.user_id)
                thumb = FSInputFile(thumb_path) if thumb_path else None

                caption = apply_template(
                    settings.get("caption", "{filename}"),
                    filename=esc(task.new_filename),
                    filesize=esc(human_size(file_size)),
                    user=esc(user.first_name),
                    id=user.id,
                    title="", season="", episode="", quality="", audio="",
                )

                upload_size = os.path.getsize(upload_path)
                upload_file = ProgressFSInputFile(upload_path, task.new_filename, reporter, upload_size, task.cancel_event)

                if output_kind == "video":
                    sent = await bot.send_video(task.chat_id, upload_file, caption=caption, thumbnail=thumb, supports_streaming=True)
                elif output_kind == "audio":
                    sent = await bot.send_audio(task.chat_id, upload_file, caption=caption, thumbnail=thumb)
                else:
                    sent = await bot.send_document(task.chat_id, upload_file, caption=caption, thumbnail=thumb)

                success = True

                await _send_to_dub_channel(bot, settings.get("dub_channel"), upload_path, task.new_filename, output_kind, thumb, caption)
                await _send_to_log_channel(bot, settings.get("log_channel"), user, task.new_filename, file_size, "SUCCESS")

                await tasks_db.update_task_status(task.task_id, "success")
                await tasks_db.bump_stat("total_renames")
                await tasks_db.bump_stat("successful_renames")
                await tasks_db.bump_stat("total_files_processed")
                await tasks_db.bump_stat("total_processing_size", file_size)

                await bot.edit_message_text("<b>File renamed successfully.</b>", chat_id=task.chat_id, message_id=status_msg.message_id)

            except TaskCancelled:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Task {task.task_id} attempt {attempt} failed: {e}")
                if attempt < config.MAX_RETRIES:
                    await reporter.set_stage(f"Retrying ({attempt}/{config.MAX_RETRIES})")
                    await asyncio.sleep(config.RETRY_DELAY_SECONDS)

        if not success:
            await tasks_db.update_task_status(task.task_id, "failed")
            await tasks_db.bump_stat("total_renames")
            await tasks_db.bump_stat("failed_renames")
            await _send_to_log_channel(bot, settings.get("log_channel"), user, task.new_filename, file_size, "FAILED")
            await bot.edit_message_text(FIXED_ERRORS["generic"], chat_id=task.chat_id, message_id=status_msg.message_id)

    except TaskCancelled:
        await tasks_db.update_task_status(task.task_id, "cancelled")
        await tasks_db.bump_stat("cancelled_tasks")
        await _send_to_log_channel(bot, settings.get("log_channel"), user, task.new_filename, file_size, "CANCELLED")
        try:
            await bot.edit_message_text(FIXED_ERRORS["cancelled"], chat_id=task.chat_id, message_id=status_msg.message_id)
        except TelegramBadRequest:
            pass

    finally:
        # Automatic cleanup — never leave partial/temp files behind.
        for p in (raw_path, final_path, metadata_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(work_dir)
        except OSError:
            pass
