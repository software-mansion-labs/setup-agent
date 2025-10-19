from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredHTMLLoader,
    TextLoader,
    UnstructuredRSTLoader,
)
from enum import Enum
from typing import List, Optional
import os
from functools import lru_cache


class SupportedExtension(str, Enum):
    MARKDOWN = ".md"
    PDF = ".pdf"
    HTML = ".html"
    TEXT = ".txt"
    RST = ".rst"

    @property
    def loader(self):
        """Return the appropriate document loader class for this file extension."""
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
    def from_str(cls, ext_str: str):
        """Convert a string extension to the corresponding enum, or None if unsupported."""
        ext_str_lower = ext_str.lower()
        return next((e for e in cls if e.value == ext_str_lower), None)

    @classmethod
    def is_supported_extension(cls, ext_str: str):
        return cls.from_str(ext_str=ext_str) is not None

    @classmethod
    @lru_cache(maxsize=1)
    def values(cls) -> List[str]:
        """Return a list of all supported file extension strings."""
        return [e.value for e in cls]


class FileLoader:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def _is_hidden_entry(self, path: str) -> bool:
        return path.startswith(".")

    def load_document(self, file_path: str) -> str:
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
            print(f"[WARN] Failed to load {file_path}: {e}")
            return ""

    def list_supported_files(self, dir_root: Optional[str] = None) -> List[str]:
        """Recursively list all supported files under dir_root (default: project root)."""
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
        """List only direct subdirectories of project_root."""
        all_dirs: List[str] = []

        try:
            for entry in os.listdir(self.project_root):
                full_path = os.path.join(self.project_root, entry)
                if not self._is_hidden_entry(entry) and os.path.isdir(full_path):
                    all_dirs.append(entry)
        except Exception as e:
            print(f"[WARN] Failed to list subdirectories: {e}")

        return all_dirs

    def list_direct_files(self, dir_path: str) -> List[str]:
        """List supported files directly inside a given directory (non-recursive)."""
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
            print(f"[WARN] Failed to list files in directory {dir_path}: {e}")

        return supported_files
