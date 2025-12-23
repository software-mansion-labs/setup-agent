import logging
from logging import Logger
from typing import Dict


class LoggerFactory:
    """Centralized logger factory using a class-based registry.

    This factory manages the creation and configuration of loggers to ensure
    consistent formatting and handler setup across the application. It maintains
    a registry to return existing logger instances when requested with the same name.

    Attributes:
        _loggers_registry (Dict[str, Logger]): A dictionary caching initialized loggers by name.
    """

    _loggers_registry: Dict[str, Logger] = {}

    @classmethod
    def get_logger(
        cls, name: str, level: int = logging.INFO, enable: bool = True
    ) -> Logger:
        """Retrieves or creates a configured logger instance.

        If a logger with the given name already exists in the registry, it updates
        its level and enabled status before returning it. If it does not exist,
        a new logger is created, formatted with a standard timestamped layout,
        and added to the registry.

        Args:
            name (str): The unique name of the logger.
            level (int): The logging level threshold. Defaults to logging.INFO.
            enable (bool): Whether the logger should be enabled. Defaults to True.

        Returns:
            Logger: The configured logger instance.
        """
        if name in cls._loggers_registry:
            logger = cls._loggers_registry[name]
            logger.setLevel(level)
            logger.disabled = not enable
            return logger

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.disabled = not enable

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False

        cls._loggers_registry[name] = logger
        return logger
