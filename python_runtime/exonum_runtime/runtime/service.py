"""Service interface."""
import abc
from typing import List

from exonum_runtime.crypto import Hash


class ServiceError(Exception):
    """Errors that can be raised by the service."""

    def __init__(self, code: int, description: str) -> None:
        super().__init__(description)
        self.code = code
        self.description = description


class Service(metaclass=abc.ABCMeta):
    """Base interface for every Exonum Python service."""

    @classmethod
    @abc.abstractclassmethod
    def new_instance(cls, name: str) -> "Service":
        """Classmethod creating a new service instance."""

    @classmethod
    @abc.abstractclassmethod
    def proto_sources(cls) -> List[str]:
        """Classmethod returning the list of protobuf source files required
        to interact with instances of this service."""

    @abc.abstractmethod
    def initialize(self, new_config: bytes) -> None:
        """Method called when a new configuration for service instance is available."""

    @abc.abstractmethod
    def execute(self, raw_tx: bytes) -> None:  # TODO return result?
        """Method execution the transaction."""

    @abc.abstractmethod
    def before_commit(self) -> None:
        """Method called before the block commit."""

    @abc.abstractmethod
    def after_commit(self) -> None:
        """Method called after the block commit."""

    @abc.abstractmethod
    def state_hashes(self) -> List[Hash]:
        """Should return hashes of indices used by service."""

    @abc.abstractmethod
    def wire_api(self) -> None:
        """Method called to create API endpoints."""
