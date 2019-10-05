"""Cryptocurrency Python Service"""
from typing import Any, List

from exonum_runtime.runtime.service import Service
from exonum_runtime.runtime.service_error import ServiceError
from exonum_runtime.runtime.transaction_context import TransactionContext
from exonum_runtime.merkledb.indices import MapIndex
from exonum_runtime.merkledb.schema import Schema, WithSchema

import service_pb2


class CryptocurrencyError(ServiceError):
    """Common errors that can occur in Cryptocurrency service."""


class CryptocurrencySchema(Schema):
    """Schema for Cryptocurrency service."""

    wallets: MapIndex


class Cryptocurrency(Service, WithSchema):
    """Simple cryptocurrency service"""

    _schema_ = CryptocurrencySchema
    _state_hash_: List[str] = []

    def initialize(self, fork: Any, config: Any) -> None:
        # No initialization required.
        pass

    @Cryptocurrency.transaction(tx_id=0, tx_name="TxCreateWallet")
    def create_wallet(self, context: TransactionContext, transaction: service_pb2.TxCreateWallet) -> None:
        """Transaction for creating a new wallet"""
        schema = self._schema_(self, context.fork)

        _wallets = schema.wallets()

        _wallet_name = transaction.name

        # TODO

    def wire_api(self) -> None:
        # No api
        pass
