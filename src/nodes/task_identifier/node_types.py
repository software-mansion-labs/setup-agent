from typing import List

from pydantic import BaseModel, Field


class DeveloperTasks(BaseModel):
    tasks: List[str] = Field(
        description=(
            "A list of high-level, meaningful goals derived from documentation (e.g., 'Run the Android app on an emulator'). "
            "Tasks should represent a complete end-to-end workflow, excluding low-level commands or administrative git actions."
        )
    )
