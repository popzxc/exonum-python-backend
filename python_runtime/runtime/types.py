"""Common types for python runtime."""
from typing import NamedTuple, Optional
from enum import IntEnum
import abc


class PythonRuntimeError(IntEnum):
    """Common runtime errors."""

    # TODO
    RUNTIME_NOT_READY = 0
    WRONG_SPEC = 1
    SERVICE_INSTALL_FAILED = 2


class ArtifactId(NamedTuple):
    """Structure that represents an Artifacd ID."""

    runtime_id: int
    name: str


class InstanceSpec(NamedTuple):
    """Structure that represents an Instance Spec"""

    name: str
    artifact: ArtifactId


class DeploymentResult(NamedTuple):
    """Structure that represents an result of the deployment process"""

    success: bool
    error: Optional[PythonRuntimeError]
    artifact_id: ArtifactId


class RuntimeInterface(metaclass=abc.ABCMeta):
    """Interface of the runtime."""

    @abc.abstractmethod
    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> Optional[PythonRuntimeError]:
        """Requests deploy of the artifact."""

    @abc.abstractmethod
    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        """Returns True if artifact is deployed and false otherwise."""

    @abc.abstractmethod
    def start_instance(self, instance_spec: InstanceSpec) -> Optional[PythonRuntimeError]:
        """Starts the instance with the provided name."""
