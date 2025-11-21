from pydantic import BaseModel
from typing import List


class PickedEntries(BaseModel):
    picked_entries: List[str]


class GuidelineFileCheck(BaseModel):
    is_guideline: bool
    reason: str
