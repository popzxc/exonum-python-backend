"""TODO"""

from typing import Optional

from exonum_runtime.ffi.merkledb import MerkledbFFI, ListIndexWrapper
from .base_index import BaseIndex


class ListIndex(BaseIndex):
    """TODO"""

    def initialize(self) -> None:
        """Initializes the ListIndex internal structure."""
        # pylint: disable=attribute-defined-outside-init
        ffi = MerkledbFFI.instance()
        self._index = ffi.list_index(self._index_id, self._access.inner())

    def __iter__(self) -> "_ListIndexIter":
        return _ListIndexIter(self._index)

    def __getitem__(self, idx: int) -> Optional[bytes]:
        return self._index.get(idx)

    @BaseIndex.mutable
    def __setitem__(self, idx: int, value: bytes) -> None:
        self._index.set_item(idx, value)

    def __len__(self) -> int:
        return self._index.len()

    @BaseIndex.mutable
    def push(self, item: bytes) -> None:
        """Adds an element to the ListIndex."""
        self._index.push(item)

    @BaseIndex.mutable
    def pop(self) -> Optional[bytes]:
        """Removes the last element from the ListIndex and returns its value
        (if list became empty, None will be returned)."""
        return self._index.pop()

    @BaseIndex.mutable
    def clear(self) -> None:
        """Removes all the elements from index."""
        self._index.clear()


class _ListIndexIter:
    def __init__(self, index: ListIndexWrapper):
        self._pos = 0
        self._index = index
        self._len = self._index.len()

    def __next__(self) -> bytes:
        if self._pos >= self._len:
            raise StopIteration

        value = self._index.get(self._pos)
        if value is None:
            raise RuntimeError("Index size changed during iteration")

        self._pos += 1

        return value
