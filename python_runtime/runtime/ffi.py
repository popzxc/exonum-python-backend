"""TODO"""
from typing import Any, Set
import ctypes as c

from .types import RuntimeInterface, DeploymentResult
from .raw_types import *


class RustFFIProvider:
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

    def __init__(self, rust_library_path: str, runtime: RuntimeInterface, ffi_callbacks: RawPythonMethods) -> None:
        self._rust_library_path = rust_library_path
        self._runtime = runtime

        c.cdll.LoadLibrary(self._rust_library_path)
        self._rust_interface = c.CDLL(self._rust_library_path)

        # Init python-side signatures.
        self._rust_interface.init_python_side.argtypes = [c.POINTER(RawPythonMethods)]
        self._rust_interface.deployment_completed.argtypes = [RawArtifactId, c.c_uint32]

        # Init python side.
        self._rust_interface.init_python_side(c.byref(ffi_callbacks))

    def _init_rust(self) -> None:
        """Initializes Python interfaces in the Rust side."""

    def deploy_completed(self, result: DeploymentResult) -> None:
        """Method to be called when deployment is completed."""
        raw_artifact = RawArtifactId.from_artifact_id(result.artifact_id)

        self._rust_interface.deployment_completed(raw_artifact, result.result.value)

    def runtime(self) -> RuntimeInterface:
        """Returns runtime."""
        return self._runtime
