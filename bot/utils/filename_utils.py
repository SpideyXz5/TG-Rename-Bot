import os
import re

_INVALID_CHARS = r'[\\/:*?"<>|]'


def sanitize_filename(name: str) -> str:
    """Strip filesystem-invalid characters, collapse whitespace/separators."""
    name = re.sub(_INVALID_CHARS, "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[._\-]{2,}", lambda m: m.group(0)[0], name)  # collapse repeated separators
    name = name.strip(" .")
    return name or "file"


def split_ext(filename: str):
    root, ext = os.path.splitext(filename)
    return root, ext


def build_output_filename(user_input: str, original_filename: str) -> str:
    """
    If the user didn't include an extension, keep the original file's extension.
    Duplicate filenames are allowed as-is (no auto "(1)" suffixing per spec).
    """
    user_input = sanitize_filename(user_input)
    _, user_ext = split_ext(user_input)
    _, original_ext = split_ext(original_filename)

    if user_ext:
        return user_input
    if original_ext:
        return f"{user_input}{original_ext}"
    return user_input
