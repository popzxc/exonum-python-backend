"""TODO"""
from typing import Optional, Any, Type, Dict
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


class Snapshot(metaclass=abc.ABCMeta):
    """TODO"""

    @abc.abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """TODO"""

    @abc.abstractmethod
    def close(self) -> None:
        """TODO"""

    def __enter__(self) -> "Snapshot":
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Any], exc_traceback: Optional[object]) -> None:
        self.close()


class Database(metaclass=abc.ABCMeta):
    """TODO"""

    _DATABASE_PROVIDER: Optional[Type["Database"]] = None
    _DATABASE_META: Optional[Dict[Any, Any]] = None

    @classmethod
    def register_database_provider(cls, database_provider: Type[Database]):
        """Registers a database backend.

        Raises an RuntimeError if backend is already registered."""
        if cls._DATABASE_PROVIDER is not None:
            raise RuntimeError("Database provider is already registered")

    @abc.abstractmethod
    def fork(self, name: str, family: Optional[str] = None) -> Fork:
        """TODO"""

    @abc.abstractmethod
    def snapshot(self, name: str, family: Optional[str] = None) -> Snapshot:
        """TODO"""
