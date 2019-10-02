"""TODO"""

import abc
from typing import Optional


class Fork(metaclass=abc.ABCMeta):
    """A write access to the database."""

    @abc.abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        """Puts a value into database."""

    @abc.abstractmethod
    def delete(self, key: bytes) -> None:
        """Removes a value from the database."""

    @abc.abstractmethod
    def merge(self) -> None:
        """Merges the fork into the database and closes it."""


class Snapshot(metaclass=abc.ABCMeta):
    """A read access to the database."""

    @abc.abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """Gets the value from the database."""

    @abc.abstractmethod
    def close(self) -> None:
        """Closes the snapshot so it won't be accessed anymore."""
