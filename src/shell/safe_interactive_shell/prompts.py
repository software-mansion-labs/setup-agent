from enum import Enum


class SafeInteractiveShellPrompts(str, Enum):
    REVIEW_COMMAND_SAFETY = """
        You are a command-line safety assistant.

        Analyze the following shell command and provide:
        1. A short description of what the command does.
        2. Whether it is SAFE to run (read-only, listing, inspecting, etc.) or UNSAFE
        (installs software, deletes/modifies files, requires sudo, etc.).

        Return your response strictly as JSON following this schema:
        {{
            "description": string,
            "safe": boolean,
            "reason": string
        }}
    """