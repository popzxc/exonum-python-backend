"""TODO"""
from typing import Optional
import ctypes as c

from exonum_runtime.ffi.c_callbacks import merkledb_allocate
from .common import BinaryData

# When working with C, it's always a compromise.
# pylint: disable=protected-access


class RawMapIndex(c.Structure):
    """TODO"""


class RawMapIndexMethods(c.Structure):
    """TODO"""

    _fields_ = [
        ("get", c.CFUNCTYPE(BinaryData, c.POINTER(RawMapIndex), BinaryData, c.c_void_p)),
        ("put", c.CFUNCTYPE(None, c.POINTER(RawMapIndex), BinaryData, BinaryData)),
        ("remove", c.CFUNCTYPE(None, c.POINTER(RawMapIndex), BinaryData)),
        ("clear", c.CFUNCTYPE(c.c_uint64, c.POINTER(RawMapIndex))),
    ]


RawMapIndex._fields_ = [("fork", c.c_void_p), ("index_name", c.c_char_p), ("methods", RawMapIndexMethods)]


class MapIndexWrapper:
    """TODO"""

    def __init__(self, inner: RawMapIndex) -> None:
        self._inner = inner

    def get(self, key: bytes) -> Optional[bytes]:
        """TODO"""
        # mypy isn't a friend of ctypes
        key = BinaryData(c.cast(key, c.POINTER(c.c_uint8)), c.c_uint64(len(key)))  # type: ignore
        result = self._inner.methods.get(self._inner, key, c.cast(merkledb_allocate, c.c_void_p))

        return result.into_bytes()

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
