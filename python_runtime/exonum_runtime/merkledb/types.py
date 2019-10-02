"""TODO"""

import ctypes as c
from typing import Optional, Any


class Access:
    """A generic access to the database."""

    def __init__(self, inner: c.c_void_p):
        self._inner = inner
        self._valid = False

    def __enter__(self) -> "Access":
        self._valid = True

        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Any], exc_traceback: Optional[object]) -> None:
        self._valid = False

    def valid(self) -> bool:
        """Returns True if access is valid and can be used."""
        return self._valid

    def inner(self) -> c.c_void_p:
        """Returns the inner access pointer."""
        if not self.valid():
            raise RuntimeError("Access is not valid anymore")

        return self._inner


class Fork(Access):
    """Write access to the database."""


class Snapshot(Access):
    """Read access to the database."""

