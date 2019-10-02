"""TODO"""
from typing import Any, Optional
import ctypes as c

from .types import Access
from ..c_callbacks import allocate, free_resource

# When working with C, it's always a compromise.
# pylint: disable=protected-access


class BinaryData(c.Structure):
    """TODO"""

    _fields_ = [("data", c.POINTER(c.c_uint8)), ("data_len", c.c_uint64)]

    def into_bytes(self) -> bytes:
        """Casts BinaryData obtained from Rust to bytes."""
        return bytes(self.data[: self.data_len])


class RawListIndex(c.Structure):
    """TODO"""


class RawListIndexMethods(c.Structure):
    """TODO"""

    AllocateFunctype = c.CFUNCTYPE(c.POINTER(c.c_uint8), c.c_uint64)

    _fields_ = [
        ("get", c.CFUNCTYPE(BinaryData, c.POINTER(RawListIndex), c.c_uint64, AllocateFunctype)),
        ("push", c.CFUNCTYPE(None, c.POINTER(RawListIndex), BinaryData)),
        ("pop", c.CFUNCTYPE(BinaryData, c.POINTER(RawListIndex), AllocateFunctype)),
        ("len", c.CFUNCTYPE(c.c_uint64, c.POINTER(RawListIndex))),
    ]


RawListIndex._fields_ = [("fork", c.c_void_p), ("index_name", c.c_char_p), ("methods", RawListIndexMethods)]


class ListIndexWrapper:
    """TODO"""

    def __init__(self, inner: RawListIndex) -> None:
        self._inner = inner

    def get(self, idx: int) -> Optional[bytes]:
        """TODO"""
        result = self._inner.methods.get(self._inner, c.c_uint64(idx), allocate)

        if not result.data:
            return None

        data = result.data[: result.data.value]

        free_resource(result.data)

        return data

    def push(self, value: bytes) -> None:
        """TODO"""
        data = BinaryData(c.cast(value, c.POINTER(c.c_uint8)), c.c_uint64(len(value)))

        self._inner.methods.push(self._inner, data)


class MerkledbFFI:
    """Merkldb wrapper over rust FFI."""

    _FFI_ENTITY = None

    # FFI is a singleton entity.
    def __new__(cls, *_args: Any) -> "MerkledbFFI":
        if cls._FFI_ENTITY is None:
            cls._FFI_ENTITY = super().__new__(cls)

        return cls._FFI_ENTITY

    @classmethod
    def instance(cls) -> "MerkledbFFI":
        """Gets an initialized instance of FFI provider."""
        if cls._FFI_ENTITY is None:
            raise RuntimeError("FFI is not initialized")
        return cls._FFI_ENTITY

    def __init__(self, rust_interface: c.CDLL) -> None:
        self._rust_interface = rust_interface

        # Init functions signatures.
        self._rust_interface.merkledb_list_index.argtypes = [c.c_void_p, c.c_char_p]
        self._rust_interface.merkledb_list_index.restype = RawListIndex
        self._rust_interface.merkledb_list_index_mut.argtypes = [c.c_void_p, c.c_char_p]
        self._rust_interface.merkledb_list_index_mut.restype = RawListIndex

    def list_index(self, name: bytes, access: Access) -> ListIndexWrapper:
        """Constructs ListIndex"""
        constructor = self._rust_interface.merkledb_list_index_mut

        raw_list_index = constructor(access._inner, c.c_char_p(name))

        return ListIndexWrapper(raw_list_index)
