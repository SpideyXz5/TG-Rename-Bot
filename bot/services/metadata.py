"""
Applies real container metadata (video/audio/subtitle track titles) using
ffmpeg's stream-copy mode — no re-encoding, so it's fast and lossless.
Works for containers that support metadata tags (MKV, MP4).
"""
import asyncio
import os
from bot.utils.logger import logger


async def apply_metadata(input_path: str, output_path: str, video_name: str, audio_name: str, subtitle_name: str) -> bool:
    """
    Returns True on success. On failure, leaves output_path untouched so the
    caller can fall back to using the original (renamed) file untouched.
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-map", "0",
        "-c", "copy",
    ]

    if video_name:
        cmd += ["-metadata:s:v:0", f"title={video_name}"]
    if audio_name:
        cmd += ["-metadata:s:a:0", f"title={audio_name}"]
    if subtitle_name:
        cmd += ["-metadata:s:s:0", f"title={subtitle_name}"]

    cmd.append(output_path)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f"ffmpeg metadata step failed: {stderr.decode(errors='ignore')[-500:]}")
            return False
        return os.path.exists(output_path)
    except FileNotFoundError:
        logger.warning("ffmpeg is not installed on this system — skipping metadata step.")
        return False
    except Exception as e:
        logger.warning(f"Metadata processing error: {e}")
        return False


def is_media_container(filename: str) -> bool:
    return filename.lower().endswith((".mkv", ".mp4", ".mov", ".m4v"))
