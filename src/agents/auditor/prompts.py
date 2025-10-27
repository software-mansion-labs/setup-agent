from enum import Enum


class AuditorPrompts(str, Enum):
    AUDITOR_DESCRIPTION = "You are responsible for verifying if the last installation or app step was completed successfully."
    VERIFICATION = """
        You are an auditor agent. Verify if the following step was successful on macOS:

        Step description: {step_description}
        Previous steps: {previous_steps_text}
        Step output:
        {step_output}

        Instructions:
        - Analyze if the step succeeded or failed. Ignore warnings, just ensure no errors occurred.
        - The output may be slightly malformed as it comes from manual reading bytes from the shell.
        Please ignore that fact and analyze if everything is logically correct.
        - If output is unclear, you may use:
            - run_command_tool - check system state or installation
            - websearch_tool - research error messages
        - Always return a JSON object in the following format:

        {{
            "success": true or false,
            "reason": "short description of what went wrong, empty if successful",
            "guidance": "short description of next steps, empty if successful"
        }}

        - If the step succeeded:
            {{
                "success": true,
                "reason": "",
                "guidance": ""
            }}
        - If the step failed:
            {{
                "success": false,
                "reason": "Directory not found",
                "guidance": "Verify the directory path and try again"
            }}

        - Do not include any explanations outside this JSON.
    """
