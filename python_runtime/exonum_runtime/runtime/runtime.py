"""TODO"""

import asyncio
from typing import Dict, Optional
import os
import sys

from exonum_runtime.crypto import KeyPair
from exonum_runtime.ffi.c_callbacks import build_callbacks
from exonum_runtime.ffi.ffi_provider import RustFFIProvider
from exonum_runtime.ffi.merkledb import MerkledbFFI
from exonum_runtime.proto import PythonArtifactSpec, ParseError

from .artifact import Artifact
from .types import (
    RuntimeInterface,
    ArtifactId,
    InstanceSpec,
    DeploymentResult,
    PythonRuntimeResult,
    InstanceDescriptor,
    CallInfo,
    StateHashAggregator,
    ArtifactProtobufSpec,
)
from .config import Configuration
from .runtime_api import RuntimeApi


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
        self._rust_ffi = RustFFIProvider(self._configuration.rust_lib_path, self, build_callbacks())
        self._merkledb_ffi = MerkledbFFI(self._rust_ffi._rust_interface)
        self._pending_deployments: Dict[ArtifactId, Artifact] = {}
        self._artifacts: Dict[ArtifactId, Artifact] = {}
        self._instances: Dict[InstanceSpec, Instance] = {}

        self._runtime_api = RuntimeApi(port=8080)

        self._init_artifacts()

        # Now we're ready to go, init python side.
        self._rust_ffi.init_rust()

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

    def _deploy_completed(self, future: asyncio.Future) -> None:
        result: DeploymentResult = future.result()

        self._rust_ffi.deploy_completed(result)
        if result.result == PythonRuntimeResult.OK:
            artifact_id = result.artifact_id
            artifact = self._pending_deployments[result.artifact_id]
            self._artifacts[artifact_id] = artifact

        # Service is removed from pending deployments no matter how deployment ended.
        del self._pending_deployments[result.artifact_id]

    # Implementation of RuntimeInterface.

    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> PythonRuntimeResult:
        try:
            spec = PythonArtifactSpec.from_bytes(artifact_spec)
        except ParseError:
            return PythonRuntimeResult.WRONG_SPEC

        artifact = Artifact(artifact_id, spec, self._configuration)

        deploy_future = self._loop.create_future()
        deploy_future.add_done_callback(self._deploy_completed)

        self._loop.create_task(artifact.deploy(deploy_future))

        self._pending_deployments[artifact_id] = artifact

        return PythonRuntimeResult.OK

    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        return artifact_id in self._artifacts

    def start_instance(self, instance_spec: InstanceSpec) -> PythonRuntimeResult:
        raise NotImplementedError

    def initialize_service(self, instance: InstanceDescriptor, parameters: bytes) -> PythonRuntimeResult:
        raise NotImplementedError

    def stop_service(self, instance: InstanceDescriptor) -> PythonRuntimeResult:
        raise NotImplementedError

    def execute(self, call_info: CallInfo, arguments: bytes) -> PythonRuntimeResult:
        raise NotImplementedError

    def artifact_protobuf_spec(self, artifact: ArtifactId) -> Optional[ArtifactProtobufSpec]:
        raise NotImplementedError

    def state_hashes(self) -> StateHashAggregator:
        raise NotImplementedError

    def before_commit(self) -> None:
        raise NotImplementedError

    def after_commit(self, service_keypair: KeyPair) -> None:
        raise NotImplementedError
