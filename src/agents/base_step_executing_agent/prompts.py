from enum import Enum


class BaseStepExecutingAgentPrompts(str, Enum):
    STEP_EXPLANATION_PROMPT = """
        You are a technical assistant analyzing workflow steps.
        You are given a step description and the suggested shell commands for that step.

        Analyze the commands and provide a brief explanation. Return JSON matching this schema:

        {{
            "purpose": "string",  # What the step is for
            "actions": "string",  # What this step will do
            "safe": "string"      # Whether these commands are safe to run
        }}
    """
