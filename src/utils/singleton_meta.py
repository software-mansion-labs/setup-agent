from typing import Optional, TypeVar, Generic
import threading

T = TypeVar("T")


class SingletonMeta(type, Generic[T]):
    """Thread-safe Singleton metaclass."""

    _instance: Optional[T] = None
    _lock = threading.Lock()

    def __call__(cls: type[T], *args, **kwargs) -> T:
        if getattr(cls, "_instance", None) is None:
            with getattr(cls, "_lock"):
                if getattr(cls, "_instance", None) is None:
                    setattr(cls, "_instance", super().__call__(*args, **kwargs))
        return getattr(cls, "_instance")
