"""TODO"""
from typing import Optional, Any, Dict, Tuple
from enum import Enum, auto as enum_auto

from .schema import Schema
from .database import Database, Fork


class SchemaAccessType(Enum):
    """Describes the type of access to the database."""

    Write = enum_auto()
    Read = enum_auto()


class SchemaAccess:
    def __init__(self, db: Database, access: SchemaAccessType):
        self._active = False
        self._db = db
        self._schema = self._db._schema
        self._access = access

        self._forks: Dict[Tuple[str, Optional[str]], Any] = dict()
        self._snapshots: Dict[Tuple[str, Optional[str]], Any] = dict()

    def __enter__(self) -> "SchemaAccess":
        self._active = True
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Any], exc_traceback: Optional[object]) -> None:
        self._active = False

        for fork in self._forks.values():
            fork.merge()

        for snapshot in self._snapshots.values():
            snapshot.close()

    def index(self, name: str, family: Optional[str] = None) -> None:  # TODO
        if not self._active:
            raise RuntimeError("Attempt to create index from a non-active IndexAccess")

        index_id = (name, family)

        handle = self._db.handle(name)

        index_type = self._schema.index_type(name)

        if index_id in self._snapshots:
            return index_type(self._snapshots[index_id], self._forks.get(index_id))

        snapshot = handle.snapshot(family)
        self._snapshots[index_id] = snapshot
        if self._access == SchemaAccessType.Write:
            fork: Optional[Fork] = handle.fork(family)
            self._forks[index_id] = fork
        else:
            fork = None

        return index_type(snapshot, fork)
