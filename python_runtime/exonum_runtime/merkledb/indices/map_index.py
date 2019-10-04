"""TODO"""

from typing import Optional

from exonum_runtime.ffi.merkledb import MerkledbFFI
from .base_index import BaseIndex


class MapIndex(BaseIndex):
    """TODO"""

    def initialize(self) -> None:
        """Initializes the MapIndex internal structure."""
        # pylint: disable=attribute-defined-outside-init
        ffi = MerkledbFFI.instance()
        self._index = ffi.map_index(self._index_id, self._access.inner())

    # TODO iteration is not yet supported
    # def __iter__(self) -> "_MapIndexIter":
    # return _MapIndexIter(self._index)

    def __getitem__(self, key: bytes) -> Optional[bytes]:
        return self._index.get(key)

    @BaseIndex.mutable
    def __setitem__(self, key: bytes, value: bytes) -> None:
        self._index.put(key, value)

    @BaseIndex.mutable
    def __delitem__(self, key: bytes) -> None:
        """Removes an element from the MapIndex."""
        self._index.remove(key)

    @BaseIndex.mutable
    def clear(self) -> None:
        """Removes all the elements from index."""
        self._index.clear()
