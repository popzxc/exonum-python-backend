"""Interface for a runtime."""

from typing import Optional
import abc

from .types import (
    ArtifactId,
    InstanceSpec,
    InstanceDescriptor,
    PythonRuntimeResult,
    StateHashAggregator,
    CallInfo,
    ArtifactProtobufSpec,
    ExecutionContext,
    RawIndexAccess,
)


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
    def initialize_service(
        self, access: RawIndexAccess, instance: InstanceDescriptor, parameters: bytes
    ) -> PythonRuntimeResult:
        """Initialize the instance."""

    @abc.abstractmethod
    def stop_service(self, instance: InstanceDescriptor) -> PythonRuntimeResult:
        """Stop the service instance."""

    @abc.abstractmethod
    def execute(self, context: ExecutionContext, call_info: CallInfo, arguments: bytes) -> PythonRuntimeResult:
        """Execute the transaction."""

    @abc.abstractmethod
    def artifact_protobuf_spec(self, artifact: ArtifactId) -> Optional[ArtifactProtobufSpec]:
        """Retrieve artifact protobuf sources."""

    @abc.abstractmethod
    def state_hashes(self, access: RawIndexAccess) -> StateHashAggregator:
        """Gets the state hashes of the every available service."""

    @abc.abstractmethod
    def before_commit(self, access: RawIndexAccess) -> None:
        """Callback to be called before the block commit."""

    @abc.abstractmethod
    def after_commit(self, access: RawIndexAccess) -> None:
        """Callback to be called after the block commit."""
