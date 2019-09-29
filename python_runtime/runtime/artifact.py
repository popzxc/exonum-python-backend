"""Module representing Artifact."""
import asyncio
from typing import Optional, Type
import os
import sys
import importlib

from .types import ArtifactId, DeploymentResult, PythonRuntimeError
from .config import Configuration
from .proto.protobuf import PythonArtifactSpec
from .service import Service


class ArtifactStartError(Exception):
    """Error to be raised when already deployed artifact can't be loaded."""


class Artifact:
    """TODO"""

    def __init__(
        self, artifact_id: ArtifactId, spec: PythonArtifactSpec, config: Configuration, already_deployed: bool = False
    ):
        self._id = artifact_id
        self._spec = spec
        self._config = config
        self._service_class: Optional[Type[Service]] = None if not already_deployed else self._get_service_class()

    async def deploy(self, future: asyncio.Future) -> None:
        """Performs the deploy process."""

        in_dir = self._config.artifacts_sources_folder
        out_dir = self._config.built_sources_folder

        tarball_path = os.path.join(in_dir, self._spec.source_wheel_name)

        # Install module using pip.
        install_command = " ".join([sys.executable, "-m", "pip", "install", tarball_path, "--target", out_dir])

        proc = await asyncio.create_subprocess_shell(
            install_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        _, _ = await proc.communicate()

        # On successfull installation pip should return 0.
        if proc.returncode != 0:
            result = DeploymentResult(
                success=False, error=PythonRuntimeError.SERVICE_INSTALL_FAILED, artifact_id=self._id
            )

            future.set_result(result)
            return

        # Try to import service library.
        try:
            service_module = importlib.import_module(self._spec.service_library_name)
        except (ModuleNotFoundError, ImportError):
            result = DeploymentResult(
                success=False, error=PythonRuntimeError.SERVICE_INSTALL_FAILED, artifact_id=self._id
            )

            future.set_result(result)
            return

        # Try to get service class.
        try:
            service = getattr(service_module, self._spec.service_class_name)

            if not issubclass(service, Service):
                raise ValueError("Not a Service subclass")

        except (ValueError, AttributeError):
            result = DeploymentResult(
                success=False, error=PythonRuntimeError.SERVICE_INSTALL_FAILED, artifact_id=self._id
            )

            future.set_result(result)
            return

        self._service_class = service
        result = DeploymentResult(success=True, error=None, artifact_id=self._id)
        future.set_result(result)

    def get_service(self) -> Type[Service]:
        """Returns service type."""
        if self._service_class is None:
            raise RuntimeError("Artifact is not yet deployed")

        return self._service_class

    def _get_service_class(self) -> Type[Service]:
        try:
            service_module = importlib.import_module(self._spec.service_library_name)
            service = getattr(service_module, self._spec.service_class_name)

            if not issubclass(service, Service):
                raise ValueError("Not a Service subclass")

            return service
        except (ModuleNotFoundError, ImportError, ValueError, AttributeError):
            raise ArtifactStartError()
