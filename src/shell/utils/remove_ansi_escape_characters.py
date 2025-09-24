import re

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

def remove_ansi_escape_characters(sequence: str) -> str:
    """
    Remove ANSI escape sequences from a given string.

    ANSI escape sequences are used in terminal text formatting
    (e.g., adding colors, bold, underline). This function strips
    those sequences, returning plain text.

    Args:
        sequence (str): The input string that may contain ANSI escape codes.

    Returns:
        str: The input string with all ANSI escape codes removed.

    Example:
        >>> remove_ansi_escape_characters("\\x1b[31mHello\\x1b[0m")
        'Hello'
    """
    return ANSI_ESCAPE_RE.sub("", sequence)
