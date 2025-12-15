import typer
from workflow_builder import WorkflowBuilder
import questionary
import os
from llm.constants import SuggestedModels, DEFAULT_MODEL

app = typer.Typer()


@app.command()
def run():
    project_root = questionary.path(
        "Where is the project root?",
        default=".",
        only_directories=True,
        validate=lambda p: True
        if os.path.exists(p) and os.path.isdir(p)
        else "Directory does not exist.",
    ).ask()

    add_guidelines = questionary.confirm(
        "Do you want to add guideline files? Otherwise agent will suggest some files.",
        default=False,
    ).ask()
    guideline_files = []

    if add_guidelines:
        while True:
            path = questionary.path(
                "Enter path to a guideline file (or press Enter to stop):",
                validate=lambda p: True
                if not p or os.path.isfile(p)
                else "Must be a valid filepath",
            ).unsafe_ask()

            if not path:
                break
            guideline_files.append(path)

    task = (
        questionary.text(
            "Enter a predefined task (optional, press Enter to skip):"
        ).unsafe_ask()
        or None
    )

    OTHER_MODEL_CHOICE = "Other"
    model = questionary.select(
        "Which LLM model should be used?",
        choices=[
            SuggestedModels.CLAUDE_SONNET_4_5.value,
            SuggestedModels.CLAUDE_OPUS_3.value,
            SuggestedModels.GPT_4o.value,
            OTHER_MODEL_CHOICE,
        ],
        default=DEFAULT_MODEL,
    ).unsafe_ask()

    if model == OTHER_MODEL_CHOICE:
        model = questionary.text("Enter model name:").unsafe_ask()

    log_file = (
        questionary.text(
            "Path to log file (optional, press Enter to skip):"
        ).unsafe_ask()
        or None
    )

    configure_advanced = questionary.confirm(
        "Do you want to configure advanced settings (tokens, temperature, timeout)?"
    ).unsafe_ask()

    max_output_tokens = None
    temperature = None
    timeout = None
    max_retries = None

    if configure_advanced:
        temp_input = questionary.text(
            "Temperature (0.0 to 1.0, optional):",
            validate=lambda val: True
            if val == ""
            or (val.replace(".", "", 1).isdigit() and 0.0 <= float(val) <= 1.0)
            else "Must be a number between 0.0 and 1.0",
        ).unsafe_ask()
        temperature = float(temp_input) if temp_input else None

        tokens_input = questionary.text(
            "Max output tokens (optional, press Enter to skip):",
            validate=lambda val: True
            if val == "" or val.isdigit()
            else "Must be a valid integer",
        ).unsafe_ask()
        max_output_tokens = int(tokens_input) if tokens_input else None

        timeout_input = questionary.text(
            "Timeout in seconds (optional, press Enter to skip):",
            validate=lambda val: True
            if val == "" or val.replace(".", "", 1).isdigit()
            else "Must be a valid number",
        ).unsafe_ask()
        timeout = float(timeout_input) if timeout_input else None

        retries_input = questionary.text(
            "Max retries (optional, press Enter to skip):",
            validate=lambda val: True
            if val == "" or val.isdigit()
            else "Must be a valid integer",
        ).unsafe_ask()
        max_retries = int(retries_input) if retries_input else None

    builder = WorkflowBuilder(
        project_root=project_root,
        guideline_files=guideline_files,
        task=task,
        model=model,
        log_file=log_file,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
    )
    builder.run("Install all required tools according to the provided guidelines.")
