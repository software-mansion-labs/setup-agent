from __future__ import annotations
from typing import Dict, Optional
from uuid import UUID, uuid1
from shell import InteractiveShell, BaseShell
from shell.security_context import SecurityContext
from utils.singleton_meta import SingletonMeta


class ShellRegistry(metaclass=SingletonMeta):
    def __init__(self, log_file: Optional[str] = None) -> None:
        self.shell_registry: Dict[UUID, BaseShell] = {}
        self.log_file = log_file
        self.security_context = SecurityContext()
        self.main_shell = InteractiveShell(
            security_context=self.security_context,
            log_file=self.log_file,
        )

    def register_new_shell(self) -> UUID:
        """
        Create a new InteractiveShell instance, register it in the registry,
        and return its unique UUID.
        """
        uuid = uuid1()

        while uuid in self.shell_registry:
            uuid = uuid1()

        shell = InteractiveShell(
            security_context=self.security_context,
            id=uuid,
            log_file=self.log_file,
        )
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

    def cleanup(self) -> None:
        for shell in self.shell_registry.values():
            shell.child.close()

    @classmethod
    def init(cls, log_file: Optional[str] = None) -> ShellRegistry:
        """Explicitly initialize the singleton."""
        return cls(log_file)

    @classmethod
    def get(cls) -> ShellRegistry:
        """Get the singleton instance. Raises if not initialized."""
        if cls._instance is None:
            raise RuntimeError(
                "ShellRegistry not initialized. Call ShellRegistry.init() first."
            )
        return cls._instance
