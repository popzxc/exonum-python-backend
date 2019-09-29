"""TODO"""
from typing import Any
import ctypes as c

from .types import ArtifactId, RuntimeInterface, DeploymentResult, InstanceSpec


class RawResult(c.Structure):
    """C representation of Result used in communication between Python and Rust."""

    _fields_ = [("success", c.c_bool), ("error_code", c.c_uint32)]


class RawArtifactId(c.Structure):
    """C representation of ArtifactId used in communication between Python and Rust."""

    _fields_ = [("runtime_id", c.c_uint32), ("name", c.c_char_p)]

    def into_artifact_id(self) -> ArtifactId:
        """Converts c-like artifact id into python-friendly form."""
        runtime_id = int(self.runtime_id)
        name = str(c.string_at(self.name), "utf-8")

        return ArtifactId(runtime_id, name)

    @classmethod
    def from_artifact_id(cls, artifact_id: ArtifactId) -> "RawArtifactId":
        """Converts python version of ArtifactID into c-compatible."""
        return cls(runtime_id=artifact_id.runtime_id, name=artifact_id.name)


class RawInstanceSpec(c.Structure):
    """C representation of InstanceSpec used in communication between Python and Rust."""

    _fields_ = [("name", c.c_char_p), ("artifact", RawArtifactId)]

    def into_instance_spec(self) -> InstanceSpec:
        """Converts c-like artifact id into python-friendly form."""
        name = str(c.string_at(self.name), "utf-8")
        artifact_id = self.artifact.into_artifact_id()

        return InstanceSpec(name, artifact_id)

    @classmethod
    def from_instance_spec(cls, instance_spec: InstanceSpec) -> "RawInstanceSpec":
        """Converts python version of ArtifactID into c-compatible."""
        raw_artifact = RawArtifactId.from_artifact_id(instance_spec.artifact)
        return cls(name=instance_spec.name, artifact=raw_artifact)


@c.CFUNCTYPE(RawResult, RawArtifactId, c.POINTER(c.c_ubyte), c.c_uint64)
def deploy_artifact(raw_artifact, raw_data, raw_data_len):  # type: ignore # Signature is one line above.
    """Function called from Rust to indicate an artifact deploy request."""
    artifact_id = raw_artifact.into_artifact_id()

    artifact_spec = bytes((c.c_ubyte * raw_data_len.value).from_buffer(raw_data)[:])

    ffi = RustFFIProvider.instance()

    result = ffi.request_deploy(artifact_id, artifact_spec)

    if result is not None:
        return RawResult(success=False, error_code=result.error.value)

    return RawResult(success=True, error_code=0)


@c.CFUNCTYPE(c.c_bool, RawArtifactId)
def is_artifact_deployed(raw_artifact):  # type: ignore # Signature is one line above.
    """Function called from Rust to check if artifact is deployed."""
    artifact_id = raw_artifact.into_artifact_id()
    ffi = RustFFIProvider.instance()

    return ffi.is_artifact_deployed(artifact_id)


@c.CFUNCTYPE(RawResult, RawInstanceSpec)
def start_service(raw_spec):  # type: ignore # Signature is one line above.
    """Function called from Rust to indicate an service start request."""
    instance_spec = raw_spec.into_instance_spec()

    ffi = RustFFIProvider.instance()

    result = ffi.start_service(instance_spec)

    if result is not None:
        return RawResult(success=False, error_code=result.error.value)

    return RawResult(success=True, error_code=0)


class RustFFIProvider(RuntimeInterface):
    """TODO"""

    _FFI_ENTITY = None

    # FFI is a singleton entity.
    def __new__(cls, *_args: Any) -> "RustFFIProvider":
        if cls._FFI_ENTITY is None:
            cls._FFI_ENTITY = super().__new__(cls)

        return cls._FFI_ENTITY

    @classmethod
    def instance(cls) -> "RustFFIProvider":
        """Gets an initialized instance of FFI provider."""
        if cls._FFI_ENTITY is None:
            raise RuntimeError("FFI is not initialized")
        return cls._FFI_ENTITY

    def __init__(self, rust_library_path: str, runtime: RuntimeInterface) -> None:
        self._rust_library_path = rust_library_path
        self._runtime = runtime

        c.cdll.LoadLibrary(self._rust_library_path)
        self._rust_interface = c.CDLL(self._rust_library_path)

    def _init_rust(self) -> None:
        """Initializes Python interfaces in the Rust side."""

    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> None:
        self._runtime.request_deploy(artifact_id, artifact_spec)

    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        return self._runtime.is_artifact_deployed(artifact_id)

    def start_instance(self, instance_spec: InstanceSpec) -> None:
        self._runtime.start_instance(instance_spec)

    def deploy_completed(self, result: DeploymentResult) -> None:
        """Method to be called when deployment is completed."""
        raw_artifact = RawArtifactId.from_artifact_id(result.artifact_id)

        if result.error is None:
            raw_result = RawResult(success=True, error_code=0)
        else:
            raw_result = RawResult(success=False, error_code=result.error.value)

        self._rust_interface.deployment_completed(raw_artifact, raw_result)
