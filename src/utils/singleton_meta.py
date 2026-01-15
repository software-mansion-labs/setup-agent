import threading
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class SingletonMeta(type, Generic[T]):
    """Thread-safe Singleton metaclass.

    This metaclass ensures that classes using it as a metaclass only have a single
    instance throughout the application lifecycle. It uses a double-checked
    locking mechanism to ensure thread safety during initialization.

    Attributes:
        _instance (Optional[T]): The single instance of the class, or None if not initialized.
        _lock (threading.Lock): A lock object used to synchronize instance creation.
    """

    _instance: Optional[T] = None
    _lock = threading.Lock()

    def __call__(cls: type[T], *args, **kwargs) -> T:
        """Controls the instance creation process.

        When the class is instantiated, this method checks if
        an instance already exists. If not, it acquires a lock and checks again
        (double-checked locking) before creating the instance.

        Args:
            *args: Variable length argument list passed to the class constructor.
            **kwargs: Arbitrary keyword arguments passed to the class constructor.

        Returns:
            T: The single existing instance of the class.
        """
        if getattr(cls, "_instance", None) is None:
            with getattr(cls, "_lock"):
                if getattr(cls, "_instance", None) is None:
                    setattr(cls, "_instance", super().__call__(*args, **kwargs))
        return getattr(cls, "_instance")
