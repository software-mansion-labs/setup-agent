from __future__ import annotations
from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredHTMLLoader,
    TextLoader,
    UnstructuredRSTLoader,
)
from enum import Enum
from typing import List, Optional, Type
import os
from functools import lru_cache
from utils.logger import LoggerFactory


class SupportedExtension(str, Enum):
    MARKDOWN = ".md"
    PDF = ".pdf"
    HTML = ".html"
    TEXT = ".txt"
    RST = ".rst"

    @property
    def loader(self) -> Optional[Type]:
        """Return the appropriate document loader class for this file extension.

        Returns:
            Optional[Type]: The LangChain document loader class,
            or None if no specific loader is mapped.
        """
        match self:
            case SupportedExtension.MARKDOWN:
                return UnstructuredMarkdownLoader
            case SupportedExtension.PDF:
                return UnstructuredPDFLoader
            case SupportedExtension.HTML:
                return UnstructuredHTMLLoader
            case SupportedExtension.TEXT:
                return TextLoader
            case SupportedExtension.RST:
                return UnstructuredRSTLoader
            case _:
                return None

    @classmethod
    def from_str(cls, ext_str: str) -> Optional[SupportedExtension]:
        """Convert a string extension to the corresponding enum.

        Args:
            ext_str (str): The file extension string.

        Returns:
            Optional[SupportedExtension]: The matching enum member, or None if unsupported.
        """
        ext_str_lower = ext_str.lower()
        return next((e for e in cls if e.value == ext_str_lower), None)

    @classmethod
    def is_supported_extension(cls, ext_str: str) -> bool:
        """Checks if a given extension string is supported.

        Args:
            ext_str (str): The extension to check.

        Returns:
            bool: True if supported, False otherwise.
        """
        return cls.from_str(ext_str=ext_str) is not None

    @classmethod
    @lru_cache(maxsize=1)
    def values(cls) -> List[str]:
        """Return a list of all supported file extension strings.

        Returns:
            List[str]: A list of strings representing supported extensions.
        """
        return [e.value for e in cls]


class FileLoader:
    """Utility class for scanning directories and loading document content.

    Handles the discovery of supported files within a project root and uses specific
    loaders to extract text content based on file type.

    Attributes:
        project_root (str): The absolute path to the root directory of the project.
        _logger (Logger): Logger instance for reporting errors and warnings.
    """

    def __init__(self, project_root: str) -> None:
        """Initializes the FileLoader.

        Args:
            project_root (str): The base directory path to scan for files.
        """
        self.project_root = project_root
        self._logger = LoggerFactory.get_logger(name="FILE_LOADER")

    def _is_hidden_entry(self, path: str) -> bool:
        """Checks if a file or directory is hidden (starts with '.').

        Args:
            path (str): The file or directory name.

        Returns:
            bool: True if the entry is hidden, False otherwise.
        """
        return path.startswith(".")

    def load_document(self, file_path: str) -> str:
        """Loads and extracts text content from a file.

        Attempts to use a specific LangChain loader based on the file extension.
        If no specific loader is found (or if loading fails gracefully), it falls
        back to reading the file as plain text.

        Args:
            file_path (str): The absolute path to the file.

        Returns:
            str: The extracted content of the file. Returns an empty string if loading fails.
        """
        _, file_extension = os.path.splitext(file_path)

        try:
            ext_enum = SupportedExtension.from_str(file_extension)

            if ext_enum and ext_enum.loader:
                loader = ext_enum.loader(file_path)
                docs = loader.load()
                return "\n\n".join(d.page_content for d in docs)
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()

        except Exception as e:
            self._logger.warning(f"Failed to load {file_path}: {e}")
            return ""

    def list_supported_files(self, dir_root: Optional[str] = None) -> List[str]:
        """Recursively lists all supported files under a directory.

        Traverses the directory tree, skipping hidden files and directories.
        Returns paths relative to the project root.

        Args:
            dir_root (Optional[str]): The directory to start searching from.
                Defaults to the project root if None.

        Returns:
            List[str]: A list of relative paths to supported files found.
        """
        if dir_root is None:
            dir_root = self.project_root

        supported_files: List[str] = []

        for root, dirs, files in os.walk(dir_root):
            files = [f for f in files if not self._is_hidden_entry(f)]
            dirs[:] = [d for d in dirs if not self._is_hidden_entry(d)]

            for file in files:
                if any(
                    file.lower().endswith(ext) for ext in SupportedExtension.values()
                ):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.project_root)
                    supported_files.append(relative_path)

        return supported_files

    def list_direct_subdirectories(self) -> List[str]:
        """Lists only the direct subdirectories of the project root.

        Ignores hidden directories.

        Returns:
            List[str]: A list of directory names (not full paths).
        """
        all_dirs: List[str] = []

        try:
            for entry in os.listdir(self.project_root):
                full_path = os.path.join(self.project_root, entry)
                if not self._is_hidden_entry(entry) and os.path.isdir(full_path):
                    all_dirs.append(entry)
        except Exception as e:
            self._logger.warning(f"Failed to list subdirectories: {e}")

        return all_dirs

    def list_direct_files(self, dir_path: str) -> List[str]:
        """List supported files directly inside a given directory (non-recursive).

        Scans a single directory for files that match supported extensions.
        Ignores hidden files.

        Args:
            dir_path (str): The absolute path of the directory to scan.

        Returns:
            List[str]: A list of paths (relative to project root) for supported files.
        """
        supported_files: List[str] = []

        try:
            for entry in os.listdir(dir_path):
                full_path = os.path.join(dir_path, entry)
                if os.path.isfile(full_path) and not self._is_hidden_entry(entry):
                    _, ext = os.path.splitext(entry)
                    if SupportedExtension.is_supported_extension(ext):
                        relative_path = os.path.relpath(full_path, self.project_root)
                        supported_files.append(relative_path)
        except Exception as e:
            self._logger.warning(f"Failed to list files in directory {dir_path}: {e}")

        return supported_files
