"""TODO"""

from typing import Optional, Dict

from runtime.merkledb.db import Database, Fork, Snapshot


class DbOptions:
    """TODO"""


class _MemoryDBFork(Fork):
    """TODO"""

    def __init__(self, entry_name: str, inner: Dict[str, Dict[bytes, bytes]]):
        self._inner = inner
        self._entry_name = entry_name
        self._storage = self._inner.get(entry_name, dict())

    def put(self, key: bytes, value: bytes) -> None:
        self._storage[key] = value

    def delete(self, key: bytes) -> None:
        if key in self._storage:
            del self._storage[key]

    def get(self, key: bytes) -> Optional[bytes]:
        return self._storage.get(key)

    def merge(self) -> None:
        self._inner[self._entry_name] = self._storage


class _MemoryDBSnapshot(Snapshot):
    """TODO"""

    def __init__(self, entry_name: str, inner: Dict[str, Dict[bytes, bytes]]):
        self._storage = inner.get(entry_name, dict())

    def get(self, key: bytes) -> Optional[bytes]:
        return self._storage.get(key)

    def close(self) -> None:
        pass


class MemoryDB(Database):
    """TODO"""

    def __init__(self) -> None:
        """TODO"""
        self._db: Dict[str, Dict[bytes, bytes]] = dict()

    def fork(self, name: str, family: Optional[str] = None) -> Fork:
        """TODO"""
        if family:
            entry_name = f"{name}_{family}"
        else:
            entry_name = f"{name}"

        return _MemoryDBFork(entry_name, self._db)

    def snapshot(self, name: str, family: Optional[str] = None) -> Snapshot:
        """TODO"""
        if family:
            entry_name = f"{name}_{family}"
        else:
            entry_name = f"{name}"

        return _MemoryDBSnapshot(entry_name, self._db)
