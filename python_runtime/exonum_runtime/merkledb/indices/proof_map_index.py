"""TODO"""

from typing import Optional

from exonum_runtime.ffi.merkledb import MerkledbFFI
from exonum_runtime.crypto import Hash
from .base_index import BaseIndex
from ..into_bytes import IntoBytes


class ProofMapIndex(BaseIndex):
    """TODO"""

    def initialize(self) -> None:
        """Initializes the ProofMapIndex internal structure."""
        # pylint: disable=attribute-defined-outside-init
        concrete_key, concrete_value = type(self)._two_index_types()
        self._concrete_key = concrete_key
        self._concrete_value = concrete_value

        ffi = MerkledbFFI.instance()
        self._index = ffi.proof_map_index(self._index_id, self._access.inner())

    # TODO iteration is not yet supported
    # def __iter__(self) -> "_ProofMapIndexIter":
    # return _ProofMapIndexIter(self._index)

    def _value_from_bytes(self, value: Optional[bytes]) -> Optional[IntoBytes]:
        if value is not None:
            return self._concrete_value.from_bytes(value)

        return None

    def __getitem__(self, key: IntoBytes) -> IntoBytes:
        value = self.get(key)

        if value is None:
            raise KeyError(f"KeyError: {key}")

        return value

    def get(self, key: IntoBytes, default: Optional[IntoBytes] = None) -> Optional[IntoBytes]:
        """Returns the value assotiated with provided key, or `default` value if there is
        no such key in the map."""
        value = self._index.get(key.into_bytes())

        if value is None:
            return default

        return self._value_from_bytes(value)

    @BaseIndex.mutable
    def __setitem__(self, key: IntoBytes, value: IntoBytes) -> None:
        self._index.put(key.into_bytes(), value.into_bytes())

    @BaseIndex.mutable
    def __delitem__(self, key: IntoBytes) -> None:
        """Removes an element from the MapIndex."""
        self._index.remove(key.into_bytes())

    @BaseIndex.mutable
    def clear(self) -> None:
        """Removes all the elements from index."""
        self._index.clear()

    def object_hash(self) -> Hash:
        """Returns object hash of the index."""
        return self._index.object_hash()
