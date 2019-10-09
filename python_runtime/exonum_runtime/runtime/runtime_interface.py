"""Interface for a runtime."""

from typing import Optional, Union
import abc

from .types import (
    ArtifactId,
    InstanceSpec,
    PythonRuntimeResult,
    StateHashAggregator,
    CallInfo,
    ArtifactProtobufSpec,
    ExecutionContext,
    RawIndexAccess,
)

from .service_error import ServiceError


class RuntimeInterface(metaclass=abc.ABCMeta):
    """Interface of the runtime."""

    @abc.abstractmethod
    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> PythonRuntimeResult:
        """Requests deploy of the artifact."""

    @abc.abstractmethod
    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        """Returns True if artifact is deployed and false otherwise."""

    @abc.abstractmethod
    def restart_instance(self, instance_spec: InstanceSpec) -> Union[PythonRuntimeResult, ServiceError]:
        """Starts the instance with the provided name (assuming that it's already has the parameters initialized)."""

    @abc.abstractmethod
    def add_service(
        self, access: RawIndexAccess, instance_spec: InstanceSpec, parameters: bytes
    ) -> Union[PythonRuntimeResult, ServiceError]:
        """Initialize the instance."""

    @abc.abstractmethod
    def execute(
        self, context: ExecutionContext, call_info: CallInfo, arguments: bytes
    ) -> Union[PythonRuntimeResult, ServiceError]:
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
