"""Service interface."""
import abc
from typing import no_type_check, List, NamedTuple, Callable, Dict, Any, Type
from enum import IntEnum
import importlib

from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError

from exonum_runtime.crypto import Hash
from exonum_runtime.interfaces import Named
from exonum_runtime.merkledb.types import Snapshot, Fork
from exonum_runtime.merkledb.schema import WithSchema

from .types import ArtifactProtobufSpec
from .transaction_context import TransactionContext


class _ServiceMeta(abc.ABCMeta):
    """Metaclass defining the Service internal structure."""


class GenericServiceError(IntEnum):
    """Enum denoting generic service errors."""

    WRONG_SERVICE_IMPLEMENTATION = 0
    MALFORMED_CONFIG = 1
    METHOD_NOT_FOUND = 2
    MALFORMED_PARAMETERS = 3


class ServiceError(Exception):
    """Base class for service errors.

    Codes for service errors must be in the 16..128 range.
    If code does not lie in that range, it will be enforced to be 128.

    Codes 0-15 is reserved for the `Service` class to describe generic
    execution errors."""

    def __init__(self, code: int) -> None:
        super().__init__("Service error")

        # We need to check that class is exactly ServiceError and not a subclass.
        # pylint: disable=unidiomatic-typecheck
        if type(self) != ServiceError and code < 16 or code > 128:
            code = 128

        self.code = code


class _TransactionRoute(NamedTuple):
    """Class denoting the handler of transaction and protobuf spec for it."""

    # Handlers are methods that accept `self` and parsed transaction message as argument.
    handler: Callable[["Service", TransactionContext, Any], None]
    # Name of the class in the `service.proto` to be used for argument deserialization.
    deserializer: str


class Service(Named, metaclass=_ServiceMeta):
    """Base interface for every Exonum Python service.

    Prerequirements:
    - Python Runtime expects the core protobuf file (which will contain transactions and config)
      to be named `service.proto`, and config message in it to be named `Config`.

    Creating your own service, you should do the following:

    - Create a class which is a subclass of `Service`.
    - Implement `proto_sources` method.
    - Implement `initialize` method (see the description of it).
    - Implement several transactions handlers and wrap them into `@YourService.transaction` decorator
      (see the description of this decorator).
    - Either derive `WithSchema` or implement `state_hash` function.
    - Implement `wire_api` method.
    - Optionally: implement `before_commit` and `after_commit` method.

    Errors raised by subclass of `Service` must be derived from `ServiceError`. Raising an error which is
    not derived from `ServiceError` will be considered an error in the service implementation, and such
    a service will be disabled.

    Example of service:

    >>> class MyService(Service, WithSchema):
    ...     _schema_ = MySchema
    ...     _state_hash_ = ["some_index", "some_other_index"]
    ...     def initialize(self, _fork: Fork, _config: service_pb2.Config) -> None:
    ...         pass
    ...     @classmethod
    ...     def proto_sources(cls) -> ArtifactProtobufSpec:
    ...          return my_impl_load_protobuf_spec()
    ...     @MyService.transaction(tx_id=0, tx_name="MyTx")
    ...     def my_tx_handler(self, _context: TransactionContext, _tx: service_pb2.MyTx) -> None:
    ...         pass
    ...     @MyService.transaction(tx_id=1, tx_name="MyTx2")
    ...     def my_tx_erroring_handler(self, _context: TransactionContext, _tx: service_pb2.MyTx2) -> None:
    ...         raise MyServiceError(code=22)

    TODO: Implementation of `wire_api` method is not listed.
    """

    __routing_table: Dict[int, _TransactionRoute] = dict()

    def __init__(self, module_name: str, fork: Fork, name: str, config: bytes):
        self.__instance_name = name
        self.__config = config
        self.__module_name = module_name

        try:
            service_module = importlib.import_module(f"{self.__module_name}.service_pb2")
            config_message_deserializer: Type[ProtobufMessage] = getattr(service_module, "Config")

            config_message = config_message_deserializer()
        except (ImportError, ModuleNotFoundError, AttributeError):
            # Service doesn't provide either "service.proto" or "Config" message.

            raise ServiceError(GenericServiceError.WRONG_SERVICE_IMPLEMENTATION.value)

        try:
            config_message.ParseFromString(config)
        except ProtobufDecodeError:
            # Unable to parse config.
            raise ServiceError(GenericServiceError.MALFORMED_CONFIG)

        self.initialize(fork, config_message)

    @abc.abstractmethod
    def initialize(self, fork: Fork, config: ProtobufMessage) -> None:
        """Method to perform initialization of the service instance.
        It must be implemented even there is no configuration for this service.

        In case of initialization error service should raise an subclass of
        ServiceError exception.

        Config will be deserialized automatically. It supposes Config structure to be
        defined as the `Config` message in `service.proto`.
        """

    @classmethod
    @abc.abstractclassmethod
    def proto_sources(cls) -> ArtifactProtobufSpec:
        """Classmethod returning the list of protobuf source files required
        to interact with instances of this service.

        During deploying of the service artifact, this method will be invoked to
        compile sources into the source folder of the artifact.

        All the protobuf module will be accessible to import as ".{proto_file_name}_pb2".
        By default you can use any Exonum core protobuf types."""

    @abc.abstractmethod
    def wire_api(self) -> None:
        """Method called to create API endpoints."""

    def before_commit(self, fork: Fork) -> None:
        """Method called before the block commit.
        Default implementation is empty."""

    def after_commit(self, snapshot: Snapshot) -> None:
        """Method called after the block commit.
        Default implementation is empty."""

    @no_type_check
    @classmethod
    def transaction(cls, tx_id: int, tx_name: str):
        """Decorator to denote transaction handler.

        Usage:

        >>> class MyService:
        >>>     @MyService.transaction(tx_id=0, tx_name="SomeTx")
        >>>     def some_tx(self, context: TransactionContext, arg: service_pb2.SomeTx):
        >>>         pass

        Methods to which this decorator is applied will be added to internal routing table,
        so Python runtime will be able to execute them.

        `tx_name` should be the name of message in the `service.proto` file, it will be used to
        deserialize transation from bytes and provide it to the handler.

        Pseudocode demonstrating the approximate algorithm of deserializtion:

        >>> import {service_name}.service_pb2 as service_proto
        >>> deserializer = getattr(service_proto, tx_name)
        >>> tx = deserializer()
        >>> tx.ParseFromString(raw_tx_bytes)
        """

        TransactionHandler = Callable[["Service", TransactionContext, Any], None]

        def decorator(func: TransactionHandler) -> TransactionHandler:
            if tx_id in cls.__routing_table:
                raise RuntimeError(f"Redefinition of transaction with id {tx_id} for service class {cls.__name__}")

            cls.__routing_table[tx_id] = _TransactionRoute(handler=func, deserializer=tx_name)
            return func

        return decorator

    def execute(self, context: TransactionContext, method_id: int, raw_tx: bytes) -> None:
        """Method execution the transaction.

        In case of execution error service should raise an subclass of
        ServiceError exception."""

        tx_route = self.__routing_table.get(method_id)

        if tx_route is None:
            # Unknown method.
            raise ServiceError(GenericServiceError.METHOD_NOT_FOUND.value)

        try:
            service_module = importlib.import_module(f"{self.__module_name}.service_pb2")
            deserializer: Type[ProtobufMessage] = getattr(service_module, tx_route.deserializer)

            transaction = deserializer()
        except (ImportError, ModuleNotFoundError, AttributeError):
            # Service doesn't provide either "service.proto" or deserializer message.

            raise ServiceError(GenericServiceError.WRONG_SERVICE_IMPLEMENTATION.value)

        try:
            transaction.ParseFromString(raw_tx)
        except ProtobufDecodeError:
            # Unable to parse tx.
            raise ServiceError(GenericServiceError.MALFORMED_CONFIG)

        tx_route.handler(self, context, transaction)

    def state_hashes(self, snapshot: Snapshot) -> List[Hash]:
        """Should return hashes of indices used by service.

        If type is derived from WithSchema, this method is deduced
        authomatically.

        Otherwise service must define this method by itself.

        Default implementation returns an empty list."""

        if isinstance(self, WithSchema):
            # We've checked that we're subclaass of WithSchema one line above.
            # pylint: disable=no-member
            return self.get_state_hashes(snapshot)

        return []

    # Implementation of `Named`
    def instance_name(self) -> str:
        return self.__instance_name
