"""Interface for classes to be converted into bytes"""

import abc


class IntoBytes(metaclass=abc.ABCMeta):
    """Interface for keys and values to be stored in MerkleDB"""

    @abc.abstractmethod
    def into_bytes(self) -> bytes:
        """Converts an object into byte sequence."""

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, data: bytes) -> "IntoBytes":
        """Converts a byte sequence into an object."""
