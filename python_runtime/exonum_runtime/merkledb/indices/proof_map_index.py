"""TODO"""

from typing import Optional

from exonum_runtime.crypto import Hash
from .base_index import BaseIndex
from ..ffi import MerkledbFFI


class ProofMapIndex(BaseIndex):
    """TODO"""

    def initialize(self) -> None:
        """Initializes the ProofMapIndex internal structure."""
        # pylint: disable=attribute-defined-outside-init
        ffi = MerkledbFFI.instance()
        self._index = ffi.proof_map_index(self._index_id, self._access)

    # TODO iteration is not yet supported
    # def __iter__(self) -> "_ProofMapIndexIter":
    # return _ProofMapIndexIter(self._index)

    def __getitem__(self, key: bytes) -> Optional[bytes]:
        return self._index.get(key)

    @BaseIndex.mutable
    def __setitem__(self, key: bytes, value: bytes) -> None:
        self._index.put(key, value)

    @BaseIndex.mutable
    def __delitem__(self, key: bytes) -> None:
        """Removes an element from the ProofMapIndex."""
        self._index.remove(key)

    @BaseIndex.mutable
    def clear(self) -> None:
        """Removes all the elements from index."""
        self._index.clear()

    def object_hash(self) -> Hash:
        """Returns object hash of the index."""
        return self._index.object_hash()
