import typer
from workflow_builder import WorkflowBuilder
from typing import List

app = typer.Typer(help="Operations for script1")

@app.command()
def run(
    project_root: str = typer.Option(
        ...,
        "--project_root",
        help="Path to the root of the project",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    guideline_files: List[str] = typer.Option(
        None,
        "--guideline_files",
        help="Path to the guidelines file",
        exists=True,
        file_okay=True,
        dir_okay=False
    )
):
    """Run the workflow builder."""
    builder = WorkflowBuilder(project_root=project_root, guideline_files=guideline_files)
    builder.run("Install all required tools according to the provided guidelines.")