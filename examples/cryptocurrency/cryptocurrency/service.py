"""Cryptocurrency Python Service"""
from typing import List, Optional, Dict, Any
import pickle
import os

from exonum_runtime.api.service_api import ServiceApi, ServiceApiContext
from exonum_runtime.crypto import PublicKey

# Runtime types
from exonum_runtime.runtime.service import Service
from exonum_runtime.runtime.service_error import ServiceError
from exonum_runtime.runtime.transaction_context import TransactionContext
from exonum_runtime.runtime.types import ArtifactProtobufSpec

# Merkledb types
from exonum_runtime.merkledb.indices import MapIndex
from exonum_runtime.merkledb.schema import Schema, WithSchema
from exonum_runtime.merkledb.into_bytes import IntoBytes
from exonum_runtime.merkledb.types import Fork

from .proto import service_pb2

INIT_BALANCE = 100

# Type checks are disabled for lines with protobuf structures because
# unfortunately protobuf-generated sources use dynamic type creation magic,
# so mypy isn't able to handle it.


class WalletKey(IntoBytes):
    """TODO"""

    def __init__(self, key: PublicKey):
        self.key = key

    def into_bytes(self) -> bytes:
        return self.key.value

    @classmethod
    def from_bytes(cls, data: bytes) -> "WalletKey":
        return WalletKey(key=PublicKey(data))


class Wallet(IntoBytes):
    """TODO"""

    def __init__(self, pub_key: PublicKey, name: str, balance: int) -> None:
        self.pub_key = pub_key
        self.name = name
        self.balance = balance

    def into_bytes(self) -> bytes:
        data = {"pub_key": self.pub_key.value, "name": self.name, "balance": self.balance}
        return pickle.dumps(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> "Wallet":
        wallet = pickle.loads(data)

        return Wallet(PublicKey(wallet["pub_key"]), wallet["name"], wallet["balance"])


class CryptocurrencyError(ServiceError):
    """Common errors that can occur in Cryptocurrency service."""

    WalletAlreadyExists = 16
    SenderNotFound = 17
    ReceiverNotFound = 18
    InsufficientCurrencyAmount = 19
    SenderSameAsReceiver = 20
    IncorrectSender = 21


class CryptocurrencySchema(Schema):
    """Schema for Cryptocurrency service."""

    wallets: MapIndex[WalletKey, Wallet]


class Cryptocurrency(Service, WithSchema):
    """Simple cryptocurrency service"""

    _schema_ = CryptocurrencySchema
    _state_hash_: List[str] = []

    def initialize(
        self, fork: Fork, config: service_pb2.Config  # type: ignore
    ) -> None:
        # No initialization required.
        pass

    @Cryptocurrency.transaction(tx_id=1, tx_name="TxCreateWallet")
    def create_wallet(
        self, context: TransactionContext, transaction: service_pb2.TxCreateWallet  # type: ignore
    ) -> None:
        """Transaction for creating a new wallet"""

        caller = context.caller.as_transaction()
        if caller is None:
            raise CryptocurrencyError(CryptocurrencyError.IncorrectSender)

        schema = self._schema_(self, context.fork)

        wallets = schema.wallets()

        wallet_key = WalletKey(caller.author)
        wallet_name = transaction.name  # type: ignore

        if wallets.get(wallet_key) is None:
            wallet = Wallet(caller.author, wallet_name, INIT_BALANCE)

            wallets[wallet_key] = wallet
        else:
            raise CryptocurrencyError(CryptocurrencyError.WalletAlreadyExists)

    @Cryptocurrency.transaction(tx_id=2, tx_name="TxTransfer")
    def transfer(
        self, context: TransactionContext, transaction: service_pb2.TxTransfer  # type: ignore
    ) -> None:
        """Transaction for creating a new wallet"""

        caller = context.caller.as_transaction()
        if caller is None:
            raise CryptocurrencyError(CryptocurrencyError.IncorrectSender)

        schema = self._schema_(self, context.fork)

        wallets = schema.wallets()

        from_key = WalletKey(caller.author)
        to_key = WalletKey(PublicKey(transaction.to.data))  # type: ignore

        sender: Optional[Wallet] = wallets.get(from_key)
        if sender is None:
            raise CryptocurrencyError(CryptocurrencyError.SenderNotFound)

        receiver: Optional[Wallet] = wallets.get(to_key)
        if receiver is None:
            raise CryptocurrencyError(CryptocurrencyError.ReceiverNotFound)

        amount = transaction.amount  # type: ignore

        if sender.balance < amount:
            raise CryptocurrencyError(CryptocurrencyError.InsufficientCurrencyAmount)

        sender.balance -= amount
        receiver.balance += amount

        print(f"Transfer between wallets: {sender.name} => {receiver.name}")

        wallets[from_key] = sender
        wallets[to_key] = receiver

    def wire_api(self) -> Optional[ServiceApi]:
        return CryptocurrencyApi()

    @classmethod
    def proto_sources(cls) -> ArtifactProtobufSpec:
        file_folder = os.path.split(__file__)[0]
        proto_folder = os.path.join(file_folder, "proto")

        return ArtifactProtobufSpec.from_folder(proto_folder)


class CryptocurrencyApi(ServiceApi):
    """API of the Cryptocurrency service"""

    @staticmethod
    def get_wallet(context: ServiceApiContext, wallet_id: str) -> Optional[Dict]:
        """Endpoing for getting a single wallet."""

        try:
            key = WalletKey(PublicKey(bytes.fromhex(wallet_id)))
        except ValueError:
            return None

        schema = Cryptocurrency.schema(context.instance_name, context.snapshot)

        wallets = schema.wallets()

        wallet = wallets.get(key)
        if wallet is None:
            return {"error": "Wallet not found"}

        return {"pub_key": wallet.pub_key.hex(), "name": wallet.name, "balance": wallet.balance}

    def public_endpoints(self) -> Dict[str, Dict[str, Any]]:
        # Wallet endpoint accepts only 32-byte hex value as string.
        endpoints = {r"/wallets/([[0-9a-fA-F]+]{64})": {"get": self.get_wallet}}

        return endpoints

    def private_endpoints(self) -> Dict[str, Dict[str, Any]]:
        return dict()
