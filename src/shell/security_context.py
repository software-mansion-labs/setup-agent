from typing import Set
from threading import Lock


class SecurityContext:
    def __init__(self) -> None:
        self._whitelist: Set[str] = set()
        self._lock = Lock()

    def add_to_whitelist(self, path: str) -> None:
        with self._lock:
            self._whitelist.add(path)

    def is_whitelisted(self, path: str) -> bool:
        with self._lock:
            return path in self._whitelist

    def get_whitelist_str(self) -> str:
        with self._lock:
            return ", ".join(self._whitelist) if self._whitelist else "None"
