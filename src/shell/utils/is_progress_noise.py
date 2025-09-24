import re

PROGRESS_RE = re.compile(r"\d{1,3}\.\d%#+\s*")
SPINNER_CHARS = set("⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇|/-\\")


def is_progress_noise(sequence: str) -> bool:
    """
    Detect spinner frames or progress bar lines in a string.

    This function identifies "progress noise" in CLI output, including:
    1. Progress bars matching the existing regex `PROGRESS_RE`
       (e.g., "23.4%###").
    2. Spinner frames, consisting entirely of characters in `SPINNER_CHARS`.
       The set includes Braille spinners (⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇) as well
       as common ASCII spinners (|, /, -, \).

    Args:
        sequence (str): The string to check.

    Returns:
        bool: True if the string is likely a spinner frame or a progress bar line,
              False otherwise.

    Examples:
        >>> is_progress_noise("23.4%###")
        True
        >>> is_progress_noise("⠙")
        True
        >>> is_progress_noise("|/-\\")
        True
        >>> is_progress_noise("Processing complete")
        False
    """

    if PROGRESS_RE.search(sequence):
        return True
    if sequence and all(ch in SPINNER_CHARS for ch in sequence.strip()):
        return True
    return False
