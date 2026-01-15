from __future__ import annotations
from typing import Dict, Optional
from uuid import UUID, uuid1
from shell import InteractiveShell, BaseShell
from shell.security_context import SecurityContext
from utils.singleton_meta import SingletonMeta


class ShellRegistry(metaclass=SingletonMeta):
    """Singleton registry for managing multiple interactive shell sessions.

    This class serves as a central hub for creating, retrieving, and managing
    lifecycle for shell instances. It maintains a main shell by default and
    allows the registration of additional shells identified by UUIDs. All shells
    share a common security context.

    Attributes:
        shell_registry (Dict[UUID, BaseShell]): A dictionary mapping UUIDs to registered shell instances.
        log_file (Optional[str]): The file path used for logging shell activities.
        security_context (SecurityContext): A shared security context (e.g., whitelist) for all shells.
        main_shell (InteractiveShell): The default primary shell instance.
    """

    def __init__(self, log_file: Optional[str] = None) -> None:
        """Initializes the registry and the main shell instance.

        Args:
            log_file (Optional[str]): Path to the log file. Defaults to None.
        """
        self.shell_registry: Dict[UUID, BaseShell] = {}
        self.log_file = log_file
        self.security_context = SecurityContext()
        self.main_shell = InteractiveShell(
            security_context=self.security_context,
            log_file=self.log_file,
        )

    def register_new_shell(self) -> UUID:
        """Creates and registers a new InteractiveShell instance.

        Generates a unique UUID, initializes a new shell sharing the registry's
        security context and log file, and stores it in the registry.

        Returns:
            UUID: The unique identifier for the newly created shell.
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
        """Retrieves a shell instance by its UUID.

        If the UUID is not provided (None) or if the UUID does not exist in the
        registry, the method defaults to returning the main shell.

        Args:
            uuid (Optional[UUID]): The unique identifier of the desired shell.

        Returns:
            BaseShell: The requested shell instance or the main shell.
        """
        if uuid is not None and uuid in self.shell_registry:
            return self.shell_registry[uuid]

        return self.main_shell

    def cleanup(self) -> None:
        """Terminates all registered shell processes.

        Iterates through all shells in the registry and closes their underlying
        child processes to ensure no zombie processes remain.
        """
        for shell in self.shell_registry.values():
            shell.child.close()

    @classmethod
    def init(cls, log_file: Optional[str] = None) -> ShellRegistry:
        """Explicitly initializes the singleton instance.

        Args:
            log_file (Optional[str]): Path to the log file. Defaults to None.

        Returns:
            ShellRegistry: The initialized singleton instance.
        """
        return cls(log_file)

    @classmethod
    def get(cls) -> ShellRegistry:
        """Retrieves the singleton instance.

        Returns:
            ShellRegistry: The existing singleton instance.

        Raises:
            RuntimeError: If the registry has not been initialized via `init()` first.
        """
        if cls._instance is None:
            raise RuntimeError(
                "ShellRegistry not initialized. Call ShellRegistry.init() first."
            )
        return cls._instance
