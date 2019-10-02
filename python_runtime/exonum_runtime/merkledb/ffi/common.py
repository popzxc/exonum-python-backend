"""TODO"""
import ctypes as c


class BinaryData(c.Structure):
    """TODO"""

    _fields_ = [("data", c.POINTER(c.c_uint8)), ("data_len", c.c_uint64)]

    def into_bytes(self) -> bytes:
        """Casts BinaryData obtained from Rust to bytes."""
        return bytes(self.data[: self.data_len])
