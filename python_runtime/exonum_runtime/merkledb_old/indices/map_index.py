"""TODO"""
from typing import Optional, Any

from exonum_runtime.merkledb_old.db import Fork, Database
from exonum_runtime.merkledb_old.index_owner import IndexOwner

from .base_index import BaseIndex


class MapIndexFork:
    """TODO"""

    # TODO support `dict` interface completely.

    def __init__(self, inner: Fork) -> None:
        self._inner = inner

    def __enter__(self) -> "MapIndexFork":
        return self

    def __exit__(self, *args: Any) -> None:
        self.merge()

    def __getitem__(self, key: bytes) -> bytes:
        value = self._inner.get(key)

        if value is None:
            raise KeyError(key)

        return value

    def __setitem__(self, key: bytes, value: bytes) -> None:
        self._inner.put(key, value)

    def __delitem__(self, key: bytes) -> None:
        self._inner.delete(key)

    def merge(self) -> None:
        """TODO"""
        self._inner.merge()


class MapIndex:
    """TODO"""

    def __init__(self, database: Database, owner: IndexOwner, name: str, family: Optional[str] = None):
        self._inner = BaseIndex(database, owner, name, family)

    def fork(self) -> MapIndexFork:
        """TODO"""
        inner = self._inner.fork()
        return MapIndexFork(inner)
