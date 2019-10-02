"""TODO"""

from typing import Optional, Any

from exonum_runtime.merkledb_old.db import Database, Fork
from exonum_runtime.merkledb_old.index_owner import IndexOwner


class ForkToken:
    """Fork token is required to create a Fork from the index.

    ForkToken is provided by Python runtime for services to perform
    operations over DB.
    
    Even though it's possible to create a ForkToken manually to allow
    yourself modifying database, such an approach will be considered
    highly incorrect.
    
    Attempt to create or merge index fork with invalidated ForkToken will
    result in raising a `ExpiredForkTokenError`.
    
    Every ForkToken is invalidated right after the execution of service
    method to which ForkToken was provided."""

    def __init__(self) -> None:
        self._valid = True

    def valid(self) -> bool:
        """Checks whether ForkToken is expired."""
        return self._valid

    def _invalidate(self) -> None:
        self._valid = False


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


"""
class SchemaMeta:
    # do some magic with cls._schema_

class CurrencyService(Service):
    _schema_ = [
        ("wallets", ProofListIndex),
        ("wallet_history, ProofListIndex),
        ("some_data", ListIndex),
    ]

    # Indices from which state hash should be calculated.
    _state_hash_ = ["wallets"]

    def transfer(self, schema: , tx):


database_name = db_folder + instance_name + index_name

# on service start runtime creates all the database indices with 

wallets = schema.wallets # returns ProofListIndex
wallets[key] = value

wallet_history = ServiceSchema.wallet_history(fork, family=b"123") # returns ProofListIndex

class IndexAccess:
    def _put()
    def _get()
    def _delete()
    def _merge()

    def __enter__()
    def __exit__()

    def __getitem__()

class Fork:
    __init__(self, database, schema_description):
        self._inner_forks = 
        for type
"""
