"""Module representing Artifact."""
import asyncio
from typing import Optional, Type, Any
import os
import sys
import importlib

from exonum_runtime.crypto import Hash
from exonum_runtime.proto import PythonArtifactSpec

from .types import ArtifactId, DeploymentResult, PythonRuntimeResult
from .config import Configuration
from .service import Service


class ArtifactLoadError(Exception):
    """Error to be raised when already deployed artifact can't be loaded."""


class Artifact:
    """TODO"""

    def __init__(self, artifact_id: ArtifactId, spec: PythonArtifactSpec, config: Configuration):
        self.spec = spec
        self._id = artifact_id
        self._config = config
        self._service_class: Optional[Type[Service]] = None

    async def deploy(self, future: asyncio.Future) -> None:
        """Performs the deploy process."""

        # Check if service is already deployed
        try:
            # Artifact is installed, no actions required.
            service_class = self._get_service_class()
            self._service_class = service_class
            result = DeploymentResult(result=PythonRuntimeResult.OK, artifact_id=self._id)
            future.set_result(result)
            return
        except ArtifactLoadError:
            # Nope, artifact is not installed, install it.
            pass

        # Install the tarball
        install_success = await self._install_tarball()

        if not install_success:
            result = DeploymentResult(result=PythonRuntimeResult.SERVICE_INSTALL_FAILED, artifact_id=self._id)

            future.set_result(result)
            return

        # Try to import service library.
        service_module = self._get_service_module()
        if service_module is None:
            result = DeploymentResult(result=PythonRuntimeResult.SERVICE_INSTALL_FAILED, artifact_id=self._id)

            future.set_result(result)
            return

        # Try to get service class.
        service = self._get_service_class_from_module(service_module)
        if service is None:
            result = DeploymentResult(result=PythonRuntimeResult.SERVICE_INSTALL_FAILED, artifact_id=self._id)

            future.set_result(result)
            return

        self._service_class = service
        result = DeploymentResult(result=PythonRuntimeResult.OK, artifact_id=self._id)
        future.set_result(result)

    async def _install_tarball(self) -> bool:
        in_dir = self._config.artifacts_sources_folder
        out_dir = self._config.built_sources_folder

        tarball_path = os.path.join(in_dir, self.spec.source_wheel_name)

        # Verify hash.
        with open(tarball_path, "rb") as raw_file:
            raw_file_content = raw_file.read()

        file_hash = Hash.hash_data(raw_file_content)
        if file_hash != self.spec.expected_hash:
            return False

        # Install module using pip.
        install_command = " ".join([sys.executable, "-m", "pip", "install", tarball_path, "--target", out_dir])

        proc = await asyncio.create_subprocess_shell(
            install_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        _, _ = await proc.communicate()

        # On successfull installation pip should return 0.
        return proc.returncode == 0

    def _get_service_module(self) -> Optional[Any]:
        try:
            service_module = importlib.import_module(self.spec.service_library_name)
            return service_module
        except (ModuleNotFoundError, ImportError):
            return None

    def _get_service_class_from_module(self, service_module: Any) -> Optional[Type[Service]]:
        try:
            service = getattr(service_module, self.spec.service_class_name)

            if not issubclass(service, Service):
                raise ValueError("Not a Service subclass")

            return service
        except (ValueError, AttributeError):
            return None

    def get_service(self) -> Type[Service]:
        """Returns service type."""
        if self._service_class is None:
            raise RuntimeError("Artifact is not yet deployed")

        return self._service_class

    def _get_service_class(self) -> Type[Service]:
        try:
            service_module = importlib.import_module(self.spec.service_library_name)
            service = getattr(service_module, self.spec.service_class_name)

            if not issubclass(service, Service):
                raise ValueError("Not a Service subclass")

            return service
        except (ModuleNotFoundError, ImportError, ValueError, AttributeError):
            raise ArtifactLoadError()
