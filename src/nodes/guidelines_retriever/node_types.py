from typing import List

from pydantic import BaseModel, Field


class PickedEntries(BaseModel):
    """A collection of file paths identified as potentially relevant."""

    picked_entries: List[str] = Field(
        description="A list of strings representing file paths that likely contain setup, installation, or contribution instructions."
    )


class GuidelineFileCheck(BaseModel):
    """The result of an in-depth content analysis of a specific file."""

    is_guideline: bool = Field(
        description="A flag indicating if the file's content actually contains actionable setup instructions, installation steps, or run commands."
    )
    reason: str = Field(
        description="A short justification for why the file was included or excluded."
    )
