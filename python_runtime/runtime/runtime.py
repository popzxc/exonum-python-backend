"""TODO"""

import asyncio
from typing import Dict, Optional, Type
import os
import sys
import importlib

from .artifact import Artifact
from .types import RuntimeInterface, ArtifactId, InstanceSpec, DeploymentResult, PythonRuntimeError
from .config import Configuration
from .ffi import RustFFIProvider
from .proto.protobuf import PythonArtifactSpec, ParseError
from .service import Service


class Instance:
    """TODO"""

    def __init__(self, instance_spec: InstanceSpec):
        self._name = instance_spec.name
        self._artifact = instance_spec.artifact


class PythonRuntime(RuntimeInterface):
    """TODO"""

    def __init__(self, loop: asyncio.AbstractEventLoop, config_path: str) -> None:
        self._loop = loop
        self._configuration = Configuration(config_path)
        self._rust_ffi = RustFFIProvider(self._configuration.rust_lib_path, self)
        self._pending_deployments: Dict[ArtifactId, Artifact] = {}
        self._artifacts: Dict[ArtifactId, Artifact] = {}
        self._instances: Dict[InstanceSpec, Instance] = {}

        self._init_artifacts()

    def _init_artifacts(self) -> None:
        # Create artifacts sources folder if needed.
        artifacts_sources_folder = self._configuration.artifacts_sources_folder
        if not os.path.exists(artifacts_sources_folder):
            os.makedirs(artifacts_sources_folder)

        # Create built artifacts folder if needed.
        built_artifacts_folder = self._configuration.built_sources_folder
        if not os.path.exists(built_artifacts_folder):
            os.makedirs(built_artifacts_folder)

        # Add built artifacts folder to the path.
        sys.path.append(built_artifacts_folder)

        # TODO load artifacts & instances (don't forget to verify hashes)

    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> Optional[PythonRuntimeError]:
        try:
            spec = PythonArtifactSpec.from_bytes(artifact_spec)
        except ParseError:
            return PythonRuntimeError.WRONG_SPEC

        artifact = Artifact(artifact_id, spec, self._configuration)

        deploy_future = self._loop.create_future()
        deploy_future.add_done_callback(self._deploy_completed)

        self._loop.create_task(artifact.deploy(deploy_future))

        self._pending_deployments[artifact_id] = artifact

        return None

    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        return artifact_id in self._artifacts

    def start_instance(self, instance_spec: InstanceSpec) -> None:
        pass

    def _deploy_completed(self, future: asyncio.Future) -> None:
        result: DeploymentResult = future.result()

        self._rust_ffi.deploy_completed(result)
        if result.success:
            artifact_id = result.artifact_id
            artifact = self._pending_deployments[result.artifact_id]
            self._artifacts[artifact_id] = artifact
            del self._pending_deployments[result.artifact_id]
