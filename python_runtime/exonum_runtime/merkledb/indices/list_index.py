"""TODO"""

from typing import Optional

from exonum_runtime.ffi.merkledb import MerkledbFFI, ListIndexWrapper
from .base_index import BaseIndex
from ..into_bytes import IntoBytes


class ListIndex(BaseIndex):
    """TODO"""

    def initialize(self) -> None:
        """Initializes the ListIndex internal structure."""
        # pylint: disable=attribute-defined-outside-init
        self._concrete = type(self)._one_index_type()

        ffi = MerkledbFFI.instance()
        self._index = ffi.list_index(self._index_id, self._access.inner())

    def __iter__(self) -> "_ListIndexIter":
        return _ListIndexIter(self._index)

    def _from_bytes(self, value: Optional[bytes]) -> Optional[IntoBytes]:
        if value is not None:
            return self._concrete.from_bytes(value)

        return None

    def __getitem__(self, idx: int) -> Optional[IntoBytes]:
        item = self._index.get(idx)

        return self._from_bytes(item)

    @BaseIndex.mutable
    def __setitem__(self, idx: int, value: IntoBytes) -> None:
        self._index.set_item(idx, value.into_bytes())

    def __len__(self) -> int:
        return self._index.len()

    @BaseIndex.mutable
    def push(self, item: IntoBytes) -> None:
        """Adds an element to the ListIndex."""
        self._index.push(item.into_bytes())

    @BaseIndex.mutable
    def append(self, item: IntoBytes) -> None:
        """Adds an element to the ListIndex."""
        self._index.push(item.into_bytes())

    @BaseIndex.mutable
    def pop(self) -> Optional[IntoBytes]:
        """Removes the last element from the ListIndex and returns its value
        (if list became empty, None will be returned)."""
        item = self._index.pop()

        return self._from_bytes(item)

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
