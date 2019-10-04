"""TODO"""
from typing import Any
import ctypes as c

from .list_index import RawListIndex, ListIndexWrapper
from .map_index import RawMapIndex, MapIndexWrapper
from .proof_list_index import RawProofListIndex, ProofListIndexWrapper
from .proof_map_index import RawProofMapIndex, ProofMapIndexWrapper

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

        self._rust_interface.merkledb_map_index.argtypes = [c.c_void_p, c.c_char_p]
        self._rust_interface.merkledb_map_index.restype = RawMapIndex

        self._rust_interface.merkledb_proof_list_index.argtypes = [c.c_void_p, c.c_char_p]
        self._rust_interface.merkledb_proof_list_index.restype = RawProofListIndex

        self._rust_interface.merkledb_proof_map_index.argtypes = [c.c_void_p, c.c_char_p]
        self._rust_interface.merkledb_proof_map_index.restype = RawProofMapIndex

    def list_index(self, name: bytes, fork: c.c_void_p) -> ListIndexWrapper:
        """Constructs ListIndex"""
        constructor = self._rust_interface.merkledb_list_index

        raw_list_index = constructor(fork, c.c_char_p(name))

        return ListIndexWrapper(raw_list_index)

    def map_index(self, name: bytes, fork: c.c_void_p) -> MapIndexWrapper:
        """Constructs MapIndex"""
        constructor = self._rust_interface.merkledb_map_index

        raw_map_index = constructor(fork, c.c_char_p(name))

        return MapIndexWrapper(raw_map_index)

    def proof_list_index(self, name: bytes, fork: c.c_void_p) -> ProofListIndexWrapper:
        """Constructs ProofListIndex"""
        constructor = self._rust_interface.merkledb_proof_list_index

        raw_list_index = constructor(fork, c.c_char_p(name))

        return ProofListIndexWrapper(raw_list_index)

    def proof_map_index(self, name: bytes, fork: c.c_void_p) -> ProofMapIndexWrapper:
        """Constructs ProofMapIndex"""
        constructor = self._rust_interface.merkledb_proof_map_index

        raw_map_index = constructor(fork, c.c_char_p(name))

        return ProofMapIndexWrapper(raw_map_index)
