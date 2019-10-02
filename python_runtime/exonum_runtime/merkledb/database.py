"""TODO"""

import abc
from typing import NamedTuple, Dict, Optional
import os

from .schema import Schema
from .types import Fork, Snapshot


class DatabaseOptions(NamedTuple):
    """DatabaseOptions is a named tuple containing the information
    needed for Database creation.

    It's not intended to be used by the end-side users."""

    folder: str
    owner: str

    def db_path(self, index_name: str) -> str:
        """Returns a full path to database."""

        return os.path.join(self.folder, f"{self.owner}_{index_name}")


class DBHandle(metaclass=abc.ABCMeta):
    """Database handler of concrete index."""

    @abc.abstractmethod
    def fork(self, family: Optional[str] = None) -> Fork:
        """Returns a Fork"""

    @abc.abstractmethod
    def snapshot(self, family: Optional[str] = None) -> Snapshot:
        """Returns a Snapshot."""


class Database(metaclass=abc.ABCMeta):
    """Base class for database implementations."""

    def __init__(self, options: DatabaseOptions, schema: Schema) -> None:
        self._schema = schema
        self._handles: Dict[str, DBHandle] = dict()

        for index_name in schema.indices():
            path = options.db_path(index_name)

            self._handles[index_name] = self.open(path)

    @abc.abstractmethod
    def open(self, path: str) -> DBHandle:
        """Creates a DBHandle managing the provided path."""

    def handle(self, index_name: str) -> DBHandle:
        """Returns the DBHandle for provided index."""
        return self._handles[index_name]

