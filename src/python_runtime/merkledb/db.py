"""TODO"""
from typing import Optional
import abc


class Fork(metaclass=abc.ABCMeta):
    """TODO"""

    @abc.abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        """TODO"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key: bytes) -> None:
        """TODO"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """TODO"""
        raise NotImplementedError


class Database(metaclass=abc.ABCMeta):
    """TODO"""

    @abc.abstractmethod
    def fork(self, name: str, family: Optional[str] = None) -> Fork:
        """TODO"""
        raise NotImplementedError
