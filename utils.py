"""
utils.py - Helper functions for the subtitle generator.
"""

import re


def format_timestamp(seconds: float) -> str:
    """
    Converts a float (seconds) to SRT timestamp format: HH:MM:SS,mmm

    Example:
        >>> format_timestamp(93.456)
        '00:01:33,456'
    """
    assert seconds >= 0, "Timestamp must be non-negative."
    milliseconds = round(seconds * 1000)

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    secs = milliseconds // 1_000
    ms = milliseconds % 1_000

    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def split_long_line(text: str, max_chars: int = 42) -> str:
    """
    Splits a subtitle line that exceeds max_chars into two lines.
    Tries to split at a logical word boundary near the midpoint.

    Example:
        >>> split_long_line("This is a very long subtitle line that needs splitting")
        'This is a very long subtitle\nline that needs splitting'
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text

    # Find the best split point (space) near the middle
    midpoint = len(text) // 2
    left = text.rfind(' ', 0, midpoint)
    right = text.find(' ', midpoint)

    if left == -1 and right == -1:
        return text  # No spaces found, return as-is

    # Choose the split point closest to the middle
    if left == -1:
        split_at = right
    elif right == -1:
        split_at = left
    else:
        split_at = left if (midpoint - left) <= (right - midpoint) else right

    line1 = text[:split_at].strip()
    line2 = text[split_at:].strip()
    return f"{line1}\n{line2}"


def sanitize_filename(path: str) -> str:
    """Strips special characters from filename for safe output path creation."""
    return re.sub(r'[^\w\s\-_./]', '', path)
