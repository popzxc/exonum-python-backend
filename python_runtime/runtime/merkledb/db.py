"""TODO"""
from typing import Optional, Any
import abc


class Fork(metaclass=abc.ABCMeta):
    """TODO"""

    @abc.abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        """TODO"""

    @abc.abstractmethod
    def delete(self, key: bytes) -> None:
        """TODO"""

    @abc.abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """TODO"""

    @abc.abstractmethod
    def merge(self) -> None:
        """TODO"""

    def __enter__(self) -> "Fork":
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Any], exc_traceback: Optional[object]) -> None:
        self.merge()


class Database(metaclass=abc.ABCMeta):
    """TODO"""

    @abc.abstractmethod
    def fork(self, name: str, family: Optional[str] = None) -> Fork:
        """TODO"""
