from io import TextIOBase
from typing import Any
from typing import Set


class SelfAwareCallable:
    """
    This distinguishes itself from a normal callable, since it knows things about itself.
    """
    # The import path of the function
    path: str

    # The variable names for its inputs
    injectable_variables: Set[str]

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """
        This is needed, since you can't inherit Callable.
        Source: https://stackoverflow.com/a/52654516/13340678
        """
        pass
