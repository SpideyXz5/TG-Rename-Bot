import html as _html


def esc(value) -> str:
    """HTML-escape any dynamic value before it's interpolated into a bold system message."""
    return _html.escape(str(value))


def hb(text: str) -> str:
    """Wrap bot-generated text in Telegram's native <b> tag (the default style for all system UI)."""
    return f"<b>{text}</b>"


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def progress_bar(percent: float, length: int = 10) -> str:
    percent = max(0, min(100, percent))
    filled = int(length * percent / 100)
    return "▰" * filled + "▱" * (length - filled)


def apply_template(template: str, **kwargs) -> str:
    """Safe .format() that never crashes on a missing/extra variable."""
    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    try:
        return template.format_map(_SafeDict(**kwargs))
    except Exception:
        return template
