"""TODO"""

from typing import NamedTuple

from exonum_runtime.merkledb.types import Fork

from .types import Caller


class TransactionContext(NamedTuple):
    """TODO"""

    fork: Fork
    caller: Caller
