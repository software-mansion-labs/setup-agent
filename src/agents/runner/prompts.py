from enum import Enum


class RunnerPrompts(str, Enum):
    RUNNER_AGENT_DESCRIPTION = (
        "You are responsible for running the next application step in a shell"
    )
    STEP_RUNNING_PROMPT = """
        Step: {step_description}
        Steps completed so far: {finished_text}

        Consider using these commands:
        {commands_text}

        Rules:
        1. Run each command sequentially in the order provided.
        2. Use tools strictly:
            - Use `run_command_tool` to run commands.
            - Use `authenticate_tool` only if a password prompt appears.
            - Use `user_input_tool` only if the step explicitly asks for non-sensitive input.
        3. If a command fails due to missing dependency, binary, or env var:
            - Stop immediately.
            - Record the failure in `errors`.
        4. Do not retry, modify commands, or suggest alternatives.
        5. Do not return commands as text — only execute with the appropriate tools.
        6. After executing commands, you must return the **final output strictly in this JSON structure** (no extra text):
        {{
            "output": "<string describing what commands were executed and their results>",
            "errors": ["<list of error messages, empty if none>"]
        }}
    """
