"""TODO"""

from typing import Optional, Any

from python_runtime.merkledb.db import Database, Fork
from python_runtime.merkledb.index_owner import IndexOwner


class BaseIndex:
    """TODO"""

    def __init__(self, database: Database, owner: IndexOwner, name: str, family: Optional[str] = None):
        self._db = database
        self._owner = owner
        self._name = name
        self._family = family

    def fork(self) -> Fork:
        """TODO"""
        index_name = self._owner.into_index_name(self._name)

        return self._db.fork(index_name, self._family)
