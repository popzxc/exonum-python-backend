"""TODO"""
from typing import Optional
import ctypes as c

from exonum_runtime.c_callbacks import allocate, free_resource
from exonum_runtime.crypto import Hash
from .common import BinaryData

# When working with C, it's always a compromise.
# pylint: disable=protected-access


class RawProofMapIndex(c.Structure):
    """TODO"""


class RawProofMapIndexMethods(c.Structure):
    """TODO"""

    AllocateFunctype = c.CFUNCTYPE(c.POINTER(c.c_uint8), c.c_uint64)

    _fields_ = [
        ("get", c.CFUNCTYPE(BinaryData, c.POINTER(RawProofMapIndex), BinaryData, AllocateFunctype)),
        ("put", c.CFUNCTYPE(None, c.POINTER(RawProofMapIndex), BinaryData, BinaryData)),
        ("remove", c.CFUNCTYPE(None, c.POINTER(RawProofMapIndex), BinaryData)),
        ("clear", c.CFUNCTYPE(c.c_uint64, c.POINTER(RawProofMapIndex))),
        ("object_hash", c.CFUNCTYPE(BinaryData, c.POINTER(RawProofMapIndex), AllocateFunctype)),
    ]


RawProofMapIndex._fields_ = [("fork", c.c_void_p), ("index_name", c.c_char_p), ("methods", RawProofMapIndexMethods)]


class ProofMapIndexWrapper:
    """TODO"""

    def __init__(self, inner: RawProofMapIndex) -> None:
        self._inner = inner

    def get(self, key: bytes) -> Optional[bytes]:
        """TODO"""
        # mypy isn't a friend of ctypes
        key = BinaryData(c.cast(key, c.POINTER(c.c_uint8)), c.c_uint64(len(key)))  # type: ignore
        result = self._inner.methods.get(self._inner, key, allocate)

        if not result.data:
            return None

        data = result.data[: result.data.value]

        free_resource(result.data)

        return data

    def put(self, key: bytes, value: bytes) -> None:
        """TODO"""
        # mypy isn't a friend of ctypes
        key = BinaryData(c.cast(key, c.POINTER(c.c_uint8)), c.c_uint64(len(key)))  # type: ignore
        value = BinaryData(c.cast(value, c.POINTER(c.c_uint8)), c.c_uint64(len(value)))  # type: ignore

        self._inner.methods.put(self._inner, key, value)

    def remove(self, key: bytes) -> None:
        """TODO"""
        # mypy isn't a friend of ctypes
        key = BinaryData(c.cast(key, c.POINTER(c.c_uint8)), c.c_uint64(len(key)))  # type: ignore
        self._inner.methods.remove(self._inner, key)

    def clear(self) -> None:
        """TODO"""
        self._inner.methods.clear(self._inner)

    def object_hash(self) -> Hash:
        """TODO"""

        result = self._inner.methods.object_hash(self._inner, allocate)

        data = result.data[: result.data.value]

        free_resource(result.data)

        return Hash(data)
