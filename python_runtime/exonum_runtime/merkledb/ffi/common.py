"""TODO"""
from typing import Optional
import ctypes as c

from exonum_runtime.c_callbacks import free_merkledb_allocated


class BinaryData(c.Structure):
    """TODO"""

    _fields_ = [("data", c.POINTER(c.c_uint8)), ("data_len", c.c_uint64)]

    def into_bytes(self) -> Optional[bytes]:
        """Casts BinaryData obtained from Rust to bytes."""

        if self.data:
            result: Optional[bytes] = bytes(self.data[: self.data_len])
        else:
            result = None

        # BinaryData objects are allocated dynamically by mekledb, so we have to
        # free allocated memory.
        free_merkledb_allocated()

        return result
