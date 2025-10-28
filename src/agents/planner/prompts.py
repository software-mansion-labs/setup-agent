from enum import Enum


class PlannerPrompts(str, Enum):
    AGENT_DESCRIPTION_PROMPT = (
        "You are responsible for analyzing README files and producing "
        "a unified step plan for the task specified by the user (mostly installing and running some project). "
        "Each step is executed by either the installer or runner agent, "
        "and all steps must be CLI-based (no App Store or GUI actions)."
    )
    FIRST_GUIDELINES_ANALYSIS = """
        You are given one or more README files for a project. Your job is to produce a unified JSON plan for executing the task defined by the user (**the GOAL**).

        Instructions:

        1. Carefully read the user-defined GOAL. Only include steps that are necessary to accomplish this GOAL.  
        - Do NOT include steps for platforms, tools, or tasks that are unrelated to the GOAL.  
        - For example, if the GOAL is “Run Android app on emulator,” do not suggest any iOS/macOS steps (i.e. do not suggest `npm pod install` if you are supposed to run an Android app)
        - If the GOAL mentions “install dependencies and run tests,” skip steps that are irrelevant to those objectives.

        2. Each step must specify which agent executes it:
        - INSTALLER_AGENT → sets up tools, dependencies, environment
        - RUNNER_AGENT → runs or starts the app

        3. Substeps:
        - Include detailed substeps with suggested CLI commands.  
        - Commands must be idempotent (safe to re-run).  
        - Prefer CLI commands over Docker or GUI actions.  
        - If a command starts a long-running process (e.g., emulator, Metro bundler, app launch), set `run_in_separate_shell: true`; otherwise, use `false`.  

        4. Include **implicit prerequisites** not mentioned in the README but necessary for success.  
        - Examples: installing Java before building Android, starting Metro Bundler before launching React Native, installing Node.js before running npm commands.

        5. Maintain correct execution order.  
        6. Exclude external links or irrelevant references.  
        7. Ignore any repository cloning instructions; the project root path is provided.  

        Output strictly as JSON with this schema:

        {{
        "plan": [
            {{
            "description": "High-level summary of the step",
            "assigned_agent": "INSTALLER_AGENT" | "RUNNER_AGENT",
            "run_in_separate_shell": true | false,
            "substeps": [
                {{
                "description": "Detailed substep description",
                "suggested_commands": ["cmd1", "cmd2"]
                }}
            ]
            }}
        ]
        }}
    """
    HANDLE_ERRORS = """
        The following errors occurred while executing previous steps.
        Adjust the plan accordingly.

        Instructions:
        1. Analyze the provided error messages carefully and determine the most probable causes.  
        - Only modify or add steps necessary to fix the errors.  
        - Do NOT remove other unrelated steps unless they are clearly redundant or incorrect.

        2. Each step must specify which agent executes it:
        - INSTALLER_AGENT → sets up tools, dependencies, environment
        - RUNNER_AGENT → runs or starts the app

        3. Substeps:
        - Include detailed substeps with suggested CLI commands.  
        - Commands must be idempotent (safe to re-run).  
        - Prefer CLI commands over Docker or GUI actions.  
        - If a command starts a long-running process (e.g., emulator, Metro bundler, app launch), set `run_in_separate_shell: true`; otherwise, use `false`.  

        4. Include **implicit prerequisites** not mentioned in the README but necessary for success.  
        - Examples: installing Java before building Android, starting Metro Bundler before launching React Native, installing Node.js before running npm commands.

        5. Maintain correct execution order.

        Return structured JSON:
        {{
        "plan": [
            {{
            "description": str,
            "assigned_agent": "INSTALLER_AGENT" | "RUNNER_AGENT",
            "run_in_separate_shell": true | false,
            "substeps": [
                {{ "description": str, "suggested_commands": [str] }}
            ]
            }}
        ]
        }}
    """
    HANDLE_FAILED_STEPS = """
        The following steps failed during execution. Adjust the unified plan to fix these failures.
        Except for new steps that will fix theses errors/issues/failures, *DO NOT FORGET to include original (failed) step* in the plan.

        1. Carefully review the failed steps and understand why they failed.  
        - You must include both the original (failed) step **and** any new steps required to fix the issue.  
        - The fix should appear immediately before or after the original failed step, depending on logical order.

        2. Each step must specify which agent executes it:
        - INSTALLER_AGENT → sets up tools, dependencies, environment
        - RUNNER_AGENT → runs or starts the app

        3. Substeps:
        - Include detailed substeps with suggested CLI commands.  
        - Commands must be idempotent (safe to re-run).  
        - Prefer CLI commands over Docker or GUI actions.  
        - If a command starts a long-running process (e.g., emulator, Metro bundler, app launch), set `run_in_separate_shell: true`; otherwise, use `false`.  

        4. Include **implicit prerequisites** not mentioned in the README but necessary for success.  
        - Examples: installing Java before building Android, starting Metro Bundler before launching React Native, installing Node.js before running npm commands.

        5. Maintain correct execution order.

        Output strictly:
        {{
        "plan": [
            {{
            "description": str,
            "assigned_agent": "INSTALLER_AGENT" | "RUNNER_AGENT",
            "run_in_separate_shell": true | false,
            "substeps": [
                {{ "description": str, "suggested_commands": [str] }}
            ]
            }}
        ]
        }}
    """
    COLLECT_USER_ERRORS = (
        "You are a planner agent helping fix installation issues.\n"
        "The user reported the following problem:\n{problem_description}\n\n"
        "Ask ONE concise clarifying question to understand the issue better.\n"
        "- Do NOT suggest any fix.\n"
        "- Do NOT output explanations.\n"
        "- If you have no further questions, return an empty string."
    )
