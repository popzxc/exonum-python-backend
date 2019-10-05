"""TODO"""

import asyncio
from typing import Dict, Optional, Tuple, Union
import os
import sys

from exonum_runtime.ffi.c_callbacks import build_callbacks
from exonum_runtime.ffi.ffi_provider import RustFFIProvider
from exonum_runtime.ffi.merkledb import MerkledbFFI
from exonum_runtime.proto import PythonArtifactSpec, ParseError
from exonum_runtime.interfaces import Named
from exonum_runtime.crypto import Hash

from exonum_runtime.merkledb.schema import Schema, WithSchema
from exonum_runtime.merkledb.indices import ProofMapIndex
from exonum_runtime.merkledb.types import Fork, Snapshot

from .artifact import Artifact
from .types import (
    ArtifactId,
    InstanceSpec,
    DeploymentResult,
    PythonRuntimeResult,
    InstanceDescriptor,
    CallInfo,
    StateHashAggregator,
    ArtifactProtobufSpec,
    ExecutionContext,
    RawIndexAccess,
    InstanceId,
)
from .config import Configuration
from .runtime_api import RuntimeApi
from .runtime_interface import RuntimeInterface
from .service import Service
from .service_error import ServiceError, GenericServiceError
from .transaction_context import TransactionContext


class PythonRuntimeSchema(Schema):
    """Python runtime schema"""

    services: ProofMapIndex


class PythonRuntime(RuntimeInterface, Named, WithSchema):
    """TODO"""

    _schema_ = PythonRuntimeSchema
    _state_hash_ = ["services"]

    def __init__(self, loop: asyncio.AbstractEventLoop, config_path: str) -> None:
        self._loop = loop
        self._configuration = Configuration(config_path)
        self._rust_ffi = RustFFIProvider(self._configuration.rust_lib_path, self, build_callbacks())
        self._merkledb_ffi = MerkledbFFI(self._rust_ffi._rust_interface)
        self._pending_deployments: Dict[ArtifactId, Artifact] = {}
        self._artifacts: Dict[ArtifactId, Artifact] = {}
        # Temporary buffer for started but not yet initialized services
        self._started_services: Dict[InstanceId, Tuple[Artifact, InstanceSpec]] = {}
        self._instances: Dict[InstanceId, Service] = {}

        # TODO
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

    # Implementation of Named.

    def instance_name(self) -> str:
        return "python_runtime"

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
        artifact_id = instance_spec.artifact
        if self.is_artifact_deployed(artifact_id):
            return PythonRuntimeResult.UNKNOWN_SERVICE

        artifact = self._artifacts[artifact_id]
        self._started_services[instance_spec.instance_id] = (artifact, instance_spec)

        return PythonRuntimeResult.OK

    def initialize_service(
        self, access: RawIndexAccess, instance: InstanceDescriptor, parameters: bytes
    ) -> Union[PythonRuntimeResult, ServiceError]:
        instance_id = instance.instance_id
        if instance_id not in self._started_services:
            # Service is attempted to initialize but not started.
            return PythonRuntimeResult.UNKNOWN_SERVICE

        fork = Fork(access)
        try:
            artifact, instance_spec = self._started_services[instance_id]
            del self._started_services[instance_id]

            service_class = artifact.get_service()
            service_instance = service_class(artifact.spec.service_library_name, fork, instance_spec.name, parameters)

            self._instances[instance_id] = service_instance

            return PythonRuntimeResult.OK
        except ServiceError as error:
            # Services are allowed to raise ServiceError to indicate that input data isn't valid.
            return error
        # Services are untrusted code, so we have to supress all the exceptions.
        except Exception:  # pylint: disable=broad-except
            # Indicate that service isn't OK.
            return ServiceError(GenericServiceError.WRONG_SERVICE_IMPLEMENTATION)

    def stop_service(self, instance: InstanceDescriptor) -> PythonRuntimeResult:
        instance_id = instance.instance_id

        if instance_id not in self._instances:
            return PythonRuntimeResult.UNKNOWN_SERVICE

        self._stop_service(instance_id)

        return PythonRuntimeResult.OK

    def _stop_service(self, instance_id: InstanceId) -> None:
        try:
            self._instances[instance_id].stop()
        # Services are untrusted code, so we have to supress all the exceptions.
        except Exception:  # pylint: disable=broad-except
            # If service didn't stop successfully, we don't care. We're removing it anyway.
            pass

        del self._instances[instance_id]

    def execute(
        self, context: ExecutionContext, call_info: CallInfo, arguments: bytes
    ) -> Union[PythonRuntimeResult, ServiceError]:
        instance_id = call_info.instance_id

        if instance_id not in self._instances:
            return PythonRuntimeResult.UNKNOWN_SERVICE

        fork = Fork(context.access)
        transaction_context = TransactionContext(fork, context.caller)

        try:
            self._instances[instance_id].execute(transaction_context, call_info.method_id, arguments)

            return PythonRuntimeResult.OK
        except ServiceError as error:
            # Services are allowed to raise ServiceError to indicate that input data isn't valid.
            return error
        # Services are untrusted code, so we have to supress all the exceptions.
        except Exception:  # pylint: disable=broad-except
            # Indicate that service isn't OK and remove it from the running instances.
            self._stop_service(instance_id)
            return ServiceError(GenericServiceError.WRONG_SERVICE_IMPLEMENTATION)

    def artifact_protobuf_spec(self, artifact: ArtifactId) -> Optional[ArtifactProtobufSpec]:
        if not self.is_artifact_deployed(artifact):
            return None

        try:
            sources = self._artifacts[artifact].get_service().proto_sources()
        except Exception:  # pylint: disable=broad-except
            return None

        # Check that service returned what we've expected.
        if not isinstance(sources, ArtifactProtobufSpec):
            return None

        return sources

    def state_hashes(self, access: RawIndexAccess) -> StateHashAggregator:

        snapshot = Snapshot(access)
        runtime = self.get_state_hashes(snapshot)

        instances = []

        for instance_id, instance in self._instances.items():
            try:
                state_hashes = instance.state_hashes(snapshot)
            except Exception:  # pylint: disable=broad-except
                # Remove service from the running instances and skip it.
                self._stop_service(instance_id)
                continue

            # Check that service returned what we expected.
            if not isinstance(state_hashes, list) or not all(map(lambda x: isinstance(x, Hash), state_hashes)):
                self._stop_service(instance_id)
                continue

            instances.append((instance_id, state_hashes))

        return StateHashAggregator(runtime, instances)

    def before_commit(self, access: RawIndexAccess) -> None:
        fork = Fork(access)

        for instance_id, instance in self._instances.items():
            try:
                instance.before_commit(fork)
            except Exception:  # pylint: disable=broad-except
                # Remove service from the running instances and skip it.
                self._stop_service(instance_id)
                continue

    def after_commit(self, access: RawIndexAccess) -> None:
        snapshot = Snapshot(access)

        for instance_id, instance in self._instances.items():
            try:
                instance.after_commit(snapshot)
            except Exception:  # pylint: disable=broad-except
                # Remove service from the running instances and skip it.
                self._stop_service(instance_id)
                continue
