"""Common types for python runtime."""
from typing import NamedTuple, NewType, Tuple, List, Optional
from enum import IntEnum
import abc

from .crypto import Hash, KeyPair


class PythonRuntimeResult(IntEnum):
    """Common runtime errors."""

    # Ok result.
    OK = 0

    # Errors emitted only by the rust part
    RUNTIME_NOT_READY = 1
    RUNTIME_DEAD = 2

    # Errors emitted by the python side
    WRONG_SPEC = 16
    SERVICE_INSTALL_FAILED = 17


class ArtifactId(NamedTuple):
    """Structure that represents an Artifacd ID."""

    runtime_id: int
    name: str


class InstanceSpec(NamedTuple):
    """Structure that represents an Instance Spec"""

    name: str
    artifact: ArtifactId


InstanceId = NewType("InstanceId", int)
MethodId = NewType("MethodId", int)


class DeploymentResult(NamedTuple):
    """Structure that represents an result of the deployment process"""

    result: PythonRuntimeResult
    artifact_id: ArtifactId


class InstanceDescriptor(NamedTuple):
    """Service Instance descriptor."""

    id: InstanceId
    name: str


class CallInfo(NamedTuple):
    """Information about service method call."""

    instance_id: InstanceId
    method_id: MethodId


class ProtoSourceFile(NamedTuple):
    """.proto file content."""

    name: str
    content: str


class ArtifactProtobufSpec(NamedTuple):
    """Proto sources of the artifact."""

    sources: List[ProtoSourceFile]


class StateHashAggregator(NamedTuple):
    """TODO"""

    # List of hashes of the root objects of the runtime information schema.
    runtime: List[Hash]
    # List of hashes of the root objects of the service instances schemas.
    instances: List[Tuple[InstanceId, List[Hash]]]


class RuntimeInterface(metaclass=abc.ABCMeta):
    """Interface of the runtime."""

    @abc.abstractmethod
    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> PythonRuntimeResult:
        """Requests deploy of the artifact."""

    @abc.abstractmethod
    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        """Returns True if artifact is deployed and false otherwise."""

    @abc.abstractmethod
    def start_instance(self, instance_spec: InstanceSpec) -> PythonRuntimeResult:
        """Starts the instance with the provided name."""

    @abc.abstractmethod
    def initialize_service(self, instance: InstanceDescriptor, parameters: bytes) -> PythonRuntimeResult:
        """Initialize the instance."""

    @abc.abstractmethod
    def stop_service(self, instance: InstanceDescriptor) -> PythonRuntimeResult:
        """Stop the service instance."""

    @abc.abstractmethod
    def execute(self, call_info: CallInfo, arguments: bytes) -> PythonRuntimeResult:
        """Execute the transaction."""

    @abc.abstractmethod
    def artifact_protobuf_spec(self, artifact: ArtifactId) -> Optional[ArtifactProtobufSpec]:
        """Retrieve artifact protobuf sources."""

    @abc.abstractmethod
    def state_hashes(self) -> StateHashAggregator:
        """Gets the state hashes of the every available service."""

    @abc.abstractmethod
    def before_commit(self) -> None:
        """Callback to be called before the block commit."""

    @abc.abstractmethod
    def after_commit(self, service_keypair: KeyPair) -> None:
        """Callback to be called after the block commit."""
