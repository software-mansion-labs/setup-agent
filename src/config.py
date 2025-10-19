from __future__ import annotations
from utils.singleton_meta import SingletonMeta
from typing import List
from pathlib import Path


class Config(metaclass=SingletonMeta):
    def __init__(
        self, project_root: str = ".", guideline_files: List[str] = []
    ) -> None:
        self.project_root = str(Path(project_root).resolve())
        self.guideline_files = [
            str(Path(file).resolve()) for file in guideline_files if Path(file).exists()
        ]

    @classmethod
    def init(cls, project_root: str = ".", guideline_files: List[str] = []) -> Config:
        return cls(project_root, guideline_files)

    @classmethod
    def get(cls) -> Config:
        if cls._instance is None:
            raise RuntimeError("Config not initialized. Call Config.init() first.")
        return cls._instance
