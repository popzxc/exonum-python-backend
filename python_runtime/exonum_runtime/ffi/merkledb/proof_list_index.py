"""TODO"""
from typing import Optional
import ctypes as c

from exonum_runtime.ffi.c_callbacks import merkledb_allocate
from exonum_runtime.crypto import Hash
from .common import BinaryData

# When working with C, it's always a compromise.
# pylint: disable=protected-access


class RawProofListIndex(c.Structure):
    """TODO"""


class RawProofListIndexMethods(c.Structure):
    """TODO"""

    AllocateFunctype = c.CFUNCTYPE(c.POINTER(c.c_uint8), c.c_uint64)

    _fields_ = [
        ("get", c.CFUNCTYPE(BinaryData, c.POINTER(RawProofListIndex), c.c_uint64, AllocateFunctype)),
        ("push", c.CFUNCTYPE(None, c.POINTER(RawProofListIndex), BinaryData)),
        # ("pop", c.CFUNCTYPE(BinaryData, c.POINTER(RawProofListIndex), AllocateFunctype)),
        ("len", c.CFUNCTYPE(c.c_uint64, c.POINTER(RawProofListIndex))),
        ("set_item", c.CFUNCTYPE(None, c.POINTER(RawProofListIndex), c.c_uint64, BinaryData)),
        ("clear", c.CFUNCTYPE(None, c.POINTER(RawProofListIndex))),
        ("object_hash", c.CFUNCTYPE(BinaryData, c.POINTER(RawProofListIndex), AllocateFunctype)),
    ]


RawProofListIndex._fields_ = [("fork", c.c_void_p), ("index_name", c.c_char_p), ("methods", RawProofListIndexMethods)]


class ProofListIndexWrapper:
    """TODO"""

    def __init__(self, inner: RawProofListIndex) -> None:
        self._inner = inner

    def get(self, idx: int) -> Optional[bytes]:
        """TODO"""
        result = self._inner.methods.get(self._inner, c.c_uint64(idx), merkledb_allocate)

        return result.into_bytes()

    def push(self, value: bytes) -> None:
        """TODO"""
        # mypy isn't a friend of ctypes
        data = BinaryData(c.cast(value, c.POINTER(c.c_uint8)), c.c_uint64(len(value)))  # type: ignore

        self._inner.methods.push(self._inner, data)

    # def pop(self) -> Optional[bytes]:
    #     """TODO"""
    #     result = self._inner.methods.pop(self._inner, allocate)

    #     return result.into_bytes()

    def len(self) -> int:
        """TODO"""
        result = self._inner.methods.len(self._inner)

        return result.value

    def set_item(self, idx: int, value: bytes) -> None:
        """TODO"""
        data = BinaryData(c.cast(value, c.POINTER(c.c_uint8)), c.c_uint64(len(value)))  # type: ignore

        self._inner.methods.set(self._inner, c.c_uint64(idx), data)

    def clear(self) -> None:
        """TODO"""
        self._inner.clear()

    def object_hash(self) -> Hash:
        """TODO"""

        result = self._inner.methods.object_hash(self._inner, merkledb_allocate)

        return Hash(result.into_bytes())
