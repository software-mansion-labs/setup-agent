from typing import Set
from threading import Lock


class SecurityContext:
    """Manages a thread-safe whitelist of allowed paths.

    This class provides mechanisms to add paths to a whitelist.

    Attributes:
        _whitelist (Set[str]): A set containing the allowed path strings.
        _lock (Lock): A threading primitive to ensure thread-safe access to the whitelist.
    """

    def __init__(self) -> None:
        """Initializes the security context with an empty whitelist."""
        self._whitelist: Set[str] = set()
        self._lock = Lock()

    def add_to_whitelist(self, path: str) -> None:
        """Adds a specific path to the allowed whitelist.

        Args:
            path (str): The path to be added.
        """
        with self._lock:
            self._whitelist.add(path)

    def is_whitelisted(self, path: str) -> bool:
        """Checks if a specific path is currently allowed.

        Args:
            path (str): The path to verify.

        Returns:
            bool: True if the path is in the whitelist, False otherwise.
        """
        with self._lock:
            return path in self._whitelist

    def get_whitelist_str(self) -> str:
        """Returns a string representation of the current whitelist.

        Returns:
            str: A comma-separated list of whitelisted paths, or "None" if the list is empty.
        """
        with self._lock:
            return ", ".join(self._whitelist) if self._whitelist else "None"
