"""TODO"""
from typing import Any
import ctypes as c

from ..types import Access
from .list_index import RawListIndex, ListIndexWrapper

# When working with C, it's always a compromise.
# pylint: disable=protected-access


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
