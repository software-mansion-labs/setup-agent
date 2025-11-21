import logging
from logging import Logger
from typing import Type, Dict, Optional


class LoggerFactory:
    """
    Centralized logger factory using a class-based registry.
    """

    _loggers_registry: Dict[str, Logger] = {}

    @classmethod
    def get_logger(
        cls, name: str, level: int = logging.INFO, enable: bool = True
    ) -> logging.Logger:
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
