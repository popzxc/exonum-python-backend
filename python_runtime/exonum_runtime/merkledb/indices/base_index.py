"""TODO"""
from typing import Optional

from ..database import Fork, Snapshot


class IndexAccessError(Exception):
    """Error to be raised when mutable access requested without Fork."""


class BaseIndex:
    """Base interface to the database for indices."""

    def __init__(self, snapshot: Snapshot, fork: Optional[Fork]) -> None:
        self._snapshot = snapshot
        self._fork = fork

    def put(self, key: bytes, value: bytes) -> None:
        """Puts a value into db."""
        if self._fork is None:
            raise IndexAccessError

        self._fork.put(key, value)

    def delete(self, key: bytes) -> None:
        """Removes a value from db."""
        if self._fork is None:
            raise IndexAccessError

        self._fork.delete(key)

    def get(self, key: bytes) -> Optional[bytes]:
        """Gets a value from db."""
        return self._snapshot.get(key)
