from enum import Enum


class BaseInteractiveShellPrompts(str, Enum):
    REVIEW_FOR_INTERACTION = """
        You are a command-line assistant. Analyze this shell output and determine
        if the system is **actually waiting for user input right now**.
    """
