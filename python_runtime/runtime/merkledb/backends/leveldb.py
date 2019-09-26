"""TODO"""

from typing import Optional, Dict, Any

import plyvel as lvldb

from runtime.merkledb.db import Database, Fork, Snapshot


class DbOptions:
    """TODO"""


class _LevelDBFork(Fork):
    """TODO"""

    def __init__(self, inner: Any):
        self._inner = inner

    def put(self, key: bytes, value: bytes) -> None:
        self._inner.put(key, value)

    def delete(self, key: bytes) -> None:
        self._inner.delete(key)

    def get(self, key: bytes) -> Optional[bytes]:
        return self._inner.get(key)

    def merge(self) -> None:
        self._inner.write()


class _LevelDBSnapshot(Snapshot):
    """TODO"""

    def __init__(self, inner: Any):
        self._inner = inner

    def get(self, key: bytes) -> Optional[bytes]:
        return self._inner.get(key)

    def close(self) -> None:
        self._inner.close()


class LevelDB(Database):
    """TODO"""

    def __init__(self, options: DbOptions):
        """TODO"""
        self._options = options

    @staticmethod
    def _get_options() -> Dict[str, Any]:
        # TODO use self._options
        options_dict = {"create_if_missing": True}

        return options_dict

    def fork(self, name: str, family: Optional[str] = None) -> Fork:
        """TODO"""
        options = self._get_options()

        options["name"] = name
        database = lvldb.DB(**options)

        if family:
            fork = database.prefixed_db(bytes(family, "utf-8")).write_batch(transaction=True)
        else:
            fork = database.write_batch(transaction=True)

        return _LevelDBFork(fork)

    def snapshot(self, name: str, family: Optional[str] = None) -> Snapshot:
        """TODO"""
        options = self._get_options()

        options["name"] = name
        database = lvldb.DB(**options)

        if family:
            snapshot = database.prefixed_db(bytes(family, "utf-8")).snapshot()
        else:
            snapshot = database.snapshot()

        return _LevelDBSnapshot(snapshot)
