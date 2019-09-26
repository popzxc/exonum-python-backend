"""TODO"""
from typing import Optional, Any

from runtime.merkledb.db import Fork, Database
from runtime.merkledb.index_owner import IndexOwner

from .base_index import BaseIndex


class ListIndexFork:
    """TODO"""

    _INDEX_BYTE_LENGTH = 4
    _INDEX_BYTE_ORDER = "big"

    def __init__(self, inner: Fork) -> None:
        self._inner = inner

        if not self._inner.get(b"length"):
            self._set_len(0)

    @classmethod
    def _int_to_bytes(cls, value: int) -> bytes:
        return value.to_bytes(cls._INDEX_BYTE_LENGTH, cls._INDEX_BYTE_ORDER)

    @classmethod
    def _bytes_to_int(cls, value: bytes) -> int:
        return int.from_bytes(value, cls._INDEX_BYTE_ORDER)

    def _set_len(self, new_len: int) -> None:
        self._inner.put(b"length", self._int_to_bytes(new_len))

    def __enter__(self) -> "ListIndexFork":
        return self

    def __exit__(self, *args: Any) -> None:
        self.merge()

    def __len__(self) -> int:
        len_bytes = self._inner.get(b"length")
        if len_bytes is None:
            raise RuntimeError("Corrupted list index")
        return self._bytes_to_int(len_bytes)

    def __getitem__(self, idx: int) -> bytes:
        value = self._inner.get(self._int_to_bytes(idx))

        if value is None:
            raise IndexError("list index out of range")

        return value

    def __setitem__(self, idx: int, value: bytes) -> None:
        if idx >= len(self):
            raise IndexError("list index out of range")

        self._inner.put(self._int_to_bytes(idx), value)

    def __delitem__(self, idx: int) -> None:
        list_len = len(self)
        if idx >= list_len:
            raise IndexError("list index out of range")

        for i in range(idx + 1, list_len):
            value = self[i]
            self[i - 1] = value

        new_list_len = list_len - 1
        self._inner.delete(self._int_to_bytes(new_list_len))
        self._set_len(new_list_len)

    def append(self, value: bytes) -> None:
        """TODO"""
        new_elem_idx = len(self)

        self._inner.put(self._int_to_bytes(new_elem_idx), value)
        self._set_len(new_elem_idx + 1)

    def merge(self) -> None:
        """TODO"""
        self._inner.merge()


class ListIndex:
    """TODO"""

    def __init__(self, database: Database, owner: IndexOwner, name: str, family: Optional[str] = None):
        self._inner = BaseIndex(database, owner, name, family)

    def fork(self) -> ListIndexFork:
        """TODO"""
        inner = self._inner.fork()
        return ListIndexFork(inner)
