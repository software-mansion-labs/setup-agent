from __future__ import annotations
from typing import Dict, Optional
from uuid import UUID, uuid1
from shell import InteractiveShell, BaseShell
from utils.singleton_meta import SingletonMeta


class ShellRegistry(metaclass=SingletonMeta):
    def __init__(self):
        self.shell_registry: Dict[UUID, BaseShell] = {}
        self.main_shell = InteractiveShell()

    def register_new_shell(self) -> UUID:
        """
        Create a new InteractiveShell instance, register it in the registry,
        and return its unique UUID.
        """
        uuid = uuid1()

        while uuid in self.shell_registry:
            uuid = uuid1()

        shell = InteractiveShell(uuid)
        self.shell_registry[uuid] = shell

        return uuid

    def get_shell(self, uuid: Optional[UUID] = None) -> BaseShell:
        """
        Retrieve a shell from the registry by its UUID.
        If no UUID is provided or the UUID is not found, return the main shell.
        """
        if uuid is not None and uuid in self.shell_registry:
            return self.shell_registry[uuid]

        return self.main_shell

    @classmethod
    def init(cls) -> ShellRegistry:
        """Explicitly initialize the singleton."""
        return cls()

    @classmethod
    def get(cls) -> ShellRegistry:
        """Get the singleton instance. Raises if not initialized."""
        if cls._instance is None:
            raise RuntimeError(
                "ShellRegistry not initialized. Call ShellRegistry.init() first."
            )
        return cls._instance
