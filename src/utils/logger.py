import logging
from logging import Logger
from typing import Type, Dict, Optional

class LoggerFactory:
    """
    Centralized logger factory using a class-based registry.
    """
    _loggers_registry: Dict[str, Logger] = {}

    @classmethod
    def get_logger(cls, name: str, level: int = logging.INFO, enable: bool = True) -> logging.Logger:
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
                "%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False

        cls._loggers_registry[name] = logger
        return logger


def with_logger(name: Optional[str] = None):
    """
    Class decorator that injects `self.logger` automatically.
    If `name` is provided, it will be used as the logger name;
    otherwise, defaults to `module.ClassName`.
    """
    def decorator(cls: Type) -> Type:
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            logger_name = name or f"{cls.__module__}.{cls.__name__}"
            self.logger = LoggerFactory.get_logger(logger_name)

        cls.__init__ = __init__
        return cls

    return decorator