from enum import Enum


class BaseInteractiveShellPrompts(str, Enum):
    REVIEW_FOR_INTERACTION = """
        You are a command-line assistant. Analyze the given shell output and determine
        whether the system is currently **waiting for user input**.

        Carefully inspect indicators such as:
        - Prompts like `>`, `$`, `#`, `>>>`, `?`, or input requests.
        - Messages asking for confirmation (e.g., "Continue? (y/n)", "Enter password:").
        - Incomplete commands or running processes waiting for input.

        Respond **strictly** in the following JSON format:

        {{
            "needs_action": true or false,
            "reason": "A concise explanation of why the shell is or is not awaiting user input."
        }}

        Example output:
        {{
            "needs_action": true,
            "reason": "The shell displays 'Enter your choice:' indicating it is waiting for user input."
        }}
    """
