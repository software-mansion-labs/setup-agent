def apply_backspaces(sequence: str) -> str:
    """
    Simulates the effect of backspace characters in a string.

    This function processes a string that may contain the backspace character (`\b`).
    Each backspace removes the most recent non-backspace character from the result,
    if one exists. If a backspace appears at the beginning of the string (when there
    are no characters to remove), it is ignored.

    Args:
        sequence (str): The input string which may contain regular characters and `\b`.

    Returns:
        str: A new string with the backspace effects applied.

    Example:
        >>> apply_backspaces("abc\bde")
        'abde'
        >>> apply_backspaces("hello\b\b\b world")
        'he world'
        >>> apply_backspaces("\b\btest")
        'test'
    """

    result = []
    for c in sequence:
        if c == "\b":
            if result:
                result.pop()
        else:
            result.append(c)

    return "".join(result)
