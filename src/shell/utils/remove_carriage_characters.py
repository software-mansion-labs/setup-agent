CARRIAGE_CHARACTER = "\r"

def remove_carriage_character(sequence: str) -> str:
    """
    Remove all carriage return characters ('\\r') from a given string.

    Args:
        sequence (str): The input string that may contain carriage return characters.

    Returns:
        str: A new string with all carriage return characters removed.
    """
    return sequence.replace(CARRIAGE_CHARACTER, "")
