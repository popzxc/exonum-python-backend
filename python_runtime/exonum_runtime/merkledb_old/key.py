"""MerkleDB key."""

import abc


class MerkleDbKey(metaclass=abc.ABCMeta):
    """Base class for keys to be stored in MerkleDB."""

    @abc.abstractmethod
    def into_bytes(self) -> bytes:
        """TODO"""

    @classmethod
    @abc.abstractclassmethod
    def from_bytes(cls, key: bytes) -> "MerkleDbKey":
        """TODO"""
