from pydantic import BaseModel
from typing import List


class DeveloperTasks(BaseModel):
    tasks: List[str]
