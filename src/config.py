from __future__ import annotations
from utils.singleton_meta import SingletonMeta
from typing import List, Optional
from pathlib import Path


class Config(metaclass=SingletonMeta):
    """Global configuration singleton for the application.

    Stores project-wide settings such as the root directory, guideline files,
    and the specific task to be executed.

    Attributes:
        project_root (str): The absolute path to the project root directory.
        guideline_files (List[str]): A list of absolute paths to existing guideline files.
        task (Optional[str]): The specific task description to run.
    """

    def __init__(
        self,
        project_root: str = ".",
        guideline_files: List[str] = [],
        task: Optional[str] = None,
    ) -> None:
        """Initializes the configuration with project settings.

        Resolves relative paths to absolute paths immediately.

        Args:
            project_root (str): The path to the project root. Defaults to current directory (".").
            guideline_files (List[str]): An optional list of paths to guidelines.
                Only files that exist are stored. Defaults to [].
            task (Optional[str]): An optional predefined task to execute. Defaults to None.
        """
        self.project_root = str(Path(project_root).resolve())
        self.guideline_files = [
            str(Path(file).resolve()) for file in guideline_files if Path(file).exists()
        ]
        self.task = task

    @classmethod
    def init(
        cls,
        project_root: str = ".",
        guideline_files: List[str] = [],
        task: Optional[str] = None,
    ) -> Config:
        """Explicitly initializes the singleton instance.

        Args:
            project_root (str): The path to the project root. Defaults to ".".
            guideline_files (List[str]): An optional list of paths to guideline files. Defaults to [].
            task (Optional[str]): An optional predefined task to run. Defaults to None.

        Returns:
            Config: The initialized singleton instance.
        """
        return cls(project_root, guideline_files, task)

    @classmethod
    def get(cls) -> Config:
        """Retrieves the singleton instance.

        Returns:
            Config: The existing configuration instance.

        Raises:
            RuntimeError: If the configuration has not been initialized via `init()` first.
        """
        if cls._instance is None:
            raise RuntimeError("Config not initialized. Call Config.init() first.")
        return cls._instance
