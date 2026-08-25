"""
Parses a source filename into {title}, {season}, {episode}, {quality}, {audio}.

Does not depend on one exact pattern — tries several common release-name
conventions (SxxExx, Season x Episode x, 1x05, etc.) and falls back
gracefully when a field can't be found.
"""
import os
import re

QUALITY_PATTERN = re.compile(r"\b(480p|720p|1080p|2160p|4k|hdrip|webrip|web-?dl|hdtv|bluray|hevc|x264|x265)\b", re.IGNORECASE)

AUDIO_LANGS = [
    "tamil", "telugu", "hindi", "english", "kannada", "malayalam",
    "japanese", "korean", "multi", "dual audio", "eng sub", "esub",
]

SEASON_EP_PATTERNS = [
    re.compile(r"[Ss](\d{1,2})[\s._-]*[Ee](\d{1,3})"),                  # S02E05 / S02.E05
    re.compile(r"[Ss]eason[\s._-]*(\d{1,2})[\s._-]*[Ee]pisode[\s._-]*(\d{1,3})", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})x(\d{1,3})\b"),                             # 1x05
]

EPISODE_ONLY_PATTERNS = [
    re.compile(r"[Ee]pisode[\s._-]*(\d{1,3})", re.IGNORECASE),
    re.compile(r"[Ee][Pp][\s._-]*(\d{1,3})\b"),
    re.compile(r"\b[Ee](\d{1,3})\b"),
]


def _find_quality(name: str):
    m = QUALITY_PATTERN.search(name)
    return m.group(1) if m else None


def _find_audio(name: str):
    lower = name.lower()
    found = [lang.title() for lang in AUDIO_LANGS if lang in lower]
    return ", ".join(found) if found else None


def _find_season_episode(name: str):
    for pattern in SEASON_EP_PATTERNS:
        m = pattern.search(name)
        if m:
            return m.group(1).zfill(2), m.group(2).zfill(2), m.start()
    for pattern in EPISODE_ONLY_PATTERNS:
        m = pattern.search(name)
        if m:
            return None, m.group(1).zfill(2), m.start()
    return None, None, None


def parse_filename(original_filename: str) -> dict:
    name, _ext = os.path.splitext(original_filename)
    working = name.replace("_", " ").replace(".", " ")

    quality = _find_quality(working)
    audio = _find_audio(working)
    season, episode, cut_index = _find_season_episode(working)

    if cut_index is not None:
        title = working[:cut_index]
    else:
        # no season/episode marker found — strip quality/audio tokens to guess the title
        title = working
        if quality:
            title = re.sub(re.escape(quality), "", title, flags=re.IGNORECASE)

    title = re.sub(r"[\[\]()._-]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip(" -_")

    return {
        "title": title or name,
        "season": season or "",
        "episode": episode or "",
        "quality": quality or "",
        "audio": audio or "",
    }
