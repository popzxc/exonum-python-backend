"""TODO"""

import asyncio
from typing import Dict, Optional, Tuple, Union, List
import os
import sys
import logging
import traceback

# Uncategorized imports
from exonum_runtime.proto import PythonArtifactSpec, ParseError
from exonum_runtime.interfaces import Named
from exonum_runtime.crypto import Hash

# API
from exonum_runtime.api.service_api import ServiceApi, ServiceApiContext, ServiceApiProvider
from exonum_runtime.api.runtime_api import RuntimeApi, RuntimeApiConfig

# FFI
from exonum_runtime.ffi.c_callbacks import build_callbacks
from exonum_runtime.ffi.ffi_provider import RustFFIProvider
from exonum_runtime.ffi.merkledb import MerkledbFFI

# Merkledb
from exonum_runtime.merkledb.schema import WithSchema
from exonum_runtime.merkledb.types import Fork, Snapshot

# Runtime
from .artifact import Artifact
from .types import (
    ArtifactId,
    InstanceSpec,
    DeploymentResult,
    PythonRuntimeResult,
    CallInfo,
    StateHashAggregator,
    ArtifactProtobufSpec,
    ExecutionContext,
    RawIndexAccess,
    InstanceId,
)
from .config import Configuration
from .runtime_interface import RuntimeInterface
from .service import Service
from .service_error import ServiceError, GenericServiceError
from .transaction_context import TransactionContext
from .runtime_schema import PythonRuntimeSchema


class PythonRuntime(RuntimeInterface, Named, WithSchema, ServiceApiProvider):
    """TODO"""

    _schema_ = PythonRuntimeSchema
    _state_hash_: List[str] = []

    def __init__(self, loop: asyncio.AbstractEventLoop, config_path: str) -> None:
        self._logger = logging.getLogger(__name__)

        self._loop = loop
        self._configuration = Configuration(config_path)
        self._rust_ffi = RustFFIProvider(self._configuration.rust_lib_path, self, build_callbacks())
        self._merkledb_ffi = MerkledbFFI(self._rust_ffi._rust_interface)
        self._pending_deployments: Dict[ArtifactId, Artifact] = {}
        self._artifacts: Dict[ArtifactId, Artifact] = {}
        # Temporary buffer for started but not yet initialized services
        self._started_services: Dict[InstanceId, Tuple[Artifact, InstanceSpec]] = {}
        self._instances: Dict[InstanceId, Service] = {}

        # API section
        api_config = RuntimeApiConfig(self._configuration.artifacts_sources_folder, self)
        self._api_snapshot = Snapshot(self._rust_ffi.snapshot_token())
        self._api_snapshot.set_always_valid()
        self._runtime_api = RuntimeApi(port=self._configuration.runtime_api_port, config=api_config)
        self._free_service_port = self._configuration.service_api_ports_start
        self._service_api: Dict[str, ServiceApi] = dict()

        # Initialization
        self._init_artifacts()

        # Now we're ready to go, init python side.
        self._rust_ffi.init_rust()
        self._logger.debug("Initialized rust part")

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

        # If this is a re-launch, dispatcher will init all the services,
        # we don't have to do it manually.

    def _deploy_completed(self, future: asyncio.Future) -> None:
        result: DeploymentResult = future.result()

        self._rust_ffi.deploy_completed(result)
        if result.result == PythonRuntimeResult.OK:
            artifact_id = result.artifact_id
            artifact = self._pending_deployments[result.artifact_id]
            self._artifacts[artifact_id] = artifact

        # Service is removed from pending deployments no matter how deployment ended.
        del self._pending_deployments[result.artifact_id]

    def _start_service_api(self, service_instance: Service) -> None:
        instance_name = service_instance.instance_name()

        self._logger.debug("Starting service api for instance %s", instance_name)
        instance_api = service_instance.wire_api()
        if instance_api is not None:
            if not isinstance(instance_api, ServiceApi):
                # Service returned not an API object.
                raise ServiceError(GenericServiceError.WRONG_SERVICE_IMPLEMENTATION)

            public_port = self._free_service_port
            private_port = self._free_service_port + 1
            self._free_service_port += 2

            context = ServiceApiContext(self._api_snapshot, instance_name)

            self._service_api[instance_name] = instance_api

            self._loop.create_task(instance_api.start(context, public_port, private_port))

    # Implementation of Named.

    def instance_name(self) -> str:
        return "python_runtime"

    # Implementation of RuntimeInterface.

    def request_deploy(self, artifact_id: ArtifactId, artifact_spec: bytes) -> PythonRuntimeResult:
        self._logger.debug("Received deploy request of artifact %s", artifact_id.name)
        try:
            spec = PythonArtifactSpec.from_bytes(artifact_spec)
        except ParseError:
            return PythonRuntimeResult.WRONG_SPEC

        self._logger.debug("Successfully parsed artifact spec %s", spec)

        artifact = Artifact(artifact_id, spec, self._configuration)

        deploy_future = self._loop.create_future()
        deploy_future.add_done_callback(self._deploy_completed)

        self._loop.create_task(artifact.deploy(deploy_future))

        self._pending_deployments[artifact_id] = artifact

        return PythonRuntimeResult.OK

    def is_artifact_deployed(self, artifact_id: ArtifactId) -> bool:
        return artifact_id in self._artifacts

    def _start_service(
        self, instance_spec: InstanceSpec, fork: Optional[Fork], parameters: Optional[bytes]
    ) -> Union[PythonRuntimeResult, ServiceError]:

        self._logger.info("Starting instance %s", instance_spec)
        artifact_id = instance_spec.artifact
        instance_id = instance_spec.instance_id
        if not self.is_artifact_deployed(artifact_id):
            self._logger.error("Request to start not deployed service: %s", instance_spec)
            return PythonRuntimeResult.UNKNOWN_SERVICE

        artifact = self._artifacts[artifact_id]
        try:
            service_class = artifact.get_service()
            service_instance = service_class(artifact.spec.service_library_name, instance_spec.name, fork, parameters)

            self._instances[instance_id] = service_instance

            self._start_service_api(service_instance)

            self._logger.info("Successfully started service: %s", instance_spec)

            return PythonRuntimeResult.OK
        except ServiceError as error:
            # Services are allowed to raise ServiceError to indicate that input data isn't valid.
            self._logger.debug("Initialize service error (emitted by service): %s", error)
            return error
        # Services are untrusted code, so we have to supress all the exceptions.
        except Exception as error:  # pylint: disable=broad-except
            # Indicate that service isn't OK.
            self._logger.warning("Initialize service error (emitted by runtime): %s", error)
            self._logger.warning("Exception traceback:\n%s", traceback.format_exc())
            return ServiceError(GenericServiceError.WRONG_SERVICE_IMPLEMENTATION)

    def restart_instance(self, instance_spec: InstanceSpec) -> Union[PythonRuntimeResult, ServiceError]:
        return self._start_service(instance_spec, None, None)

    def add_service(
        self, access: RawIndexAccess, instance_spec: InstanceSpec, parameters: bytes
    ) -> Union[PythonRuntimeResult, ServiceError]:
        with Fork(access) as fork:
            assert isinstance(fork, Fork)
            return self._start_service(instance_spec, fork, parameters)

    def _stop_service(self, instance_id: InstanceId, force: bool = True) -> None:
        if force:
            self._logger.info("Stopping service instance %s due to unallowed error raised", instance_id)
        else:
            self._logger.info("Stopping service instance %s", instance_id)

        try:
            self._instances[instance_id].stop()
        # Services are untrusted code, so we have to supress all the exceptions.
        except Exception as error:  # pylint: disable=broad-except
            # If service didn't stop successfully, we don't care. We're removing it anyway.
            self._logger.warning("Stop service error (emitted by runtime): %s. Service will be disabled anyway", error)
            self._logger.warning("Exception traceback:\n%s", traceback.format_exc())

        del self._instances[instance_id]
        self._logger.debug("Stopped service instance %s", instance_id)

    def execute(
        self, context: ExecutionContext, call_info: CallInfo, arguments: bytes
    ) -> Union[PythonRuntimeResult, ServiceError]:
        instance_id = call_info.instance_id

        if instance_id not in self._instances:
            self._logger.error("Received execute request for service %s which is not running", instance_id)
            return PythonRuntimeResult.UNKNOWN_SERVICE

        with Fork(context.access) as fork:
            assert isinstance(fork, Fork)
            transaction_context = TransactionContext(fork, context.caller)

            try:
                self._instances[instance_id].execute(transaction_context, call_info.method_id, arguments)

                return PythonRuntimeResult.OK
            except ServiceError as error:
                # Services are allowed to raise ServiceError to indicate that input data isn't valid.
                self._logger.debug("Execute service error (emitted by service): %s", error)
                return error
            # Services are untrusted code, so we have to supress all the exceptions.
            except Exception as error:  # pylint: disable=broad-except
                # Indicate that service isn't OK and remove it from the running instances.
                self._logger.warning("Execute service error (emitted by runtime): %s", error)
                self._logger.warning("Exception traceback:\n%s", traceback.format_exc())
                self._stop_service(instance_id, force=True)
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

        with Snapshot(access) as snapshot:
            assert isinstance(snapshot, Snapshot)
            runtime = self.get_state_hashes(snapshot)

            instances = []
            to_stop = []

            for instance_id, instance in self._instances.items():
                try:
                    state_hashes = instance.state_hashes(snapshot)
                except Exception as error:  # pylint: disable=broad-except
                    # Remove service from the running instances and skip it.
                    self._logger.warning("State hash service error (emitted by runtime): %s", error)
                    self._logger.warning("Exception traceback:\n%s", traceback.format_exc())
                    to_stop.append(instance_id)
                    continue

                # Check that service returned what we expected.
                if not isinstance(state_hashes, list) or not all(map(lambda x: isinstance(x, Hash), state_hashes)):
                    self._logger.warning("Service %s returned incorrect object instead of state hashes", instance_id)
                    to_stop.append(instance_id)
                    continue

                instances.append((instance_id, state_hashes))

            for instance_id in to_stop:
                # Stop failed instances.
                self._stop_service(instance_id)

        return StateHashAggregator(runtime, instances)

    def before_commit(self, access: RawIndexAccess) -> None:
        with Fork(access) as fork:
            assert isinstance(fork, Fork)

            to_stop = []

            for instance_id, instance in self._instances.items():
                try:
                    instance.before_commit(fork)
                except Exception as error:  # pylint: disable=broad-except
                    # Remove service from the running instances and skip it.
                    self._logger.warning("Service %s errored with an error %s during before_commit", instance_id, error)
                    to_stop.append(instance_id)
                    continue

            for instance_id in to_stop:
                # Stop failed instances.
                self._stop_service(instance_id)

    def after_commit(self, access: RawIndexAccess) -> None:
        with Snapshot(access) as snapshot:
            assert isinstance(snapshot, Snapshot)

            to_stop = []

            for instance_id, instance in self._instances.items():
                try:
                    instance.after_commit(snapshot)
                except Exception as error:  # pylint: disable=broad-except
                    # Remove service from the running instances and skip it.
                    self._logger.warning("Service %s errored with an error %s during after_commit", instance_id, error)
                    to_stop.append(instance_id)
                    continue

            for instance_id in to_stop:
                # Stop failed instances.
                self._stop_service(instance_id)

    # Implementation of ServiceApiProvider
    def service_api_map(self) -> Dict[str, ServiceApi]:
        """Returns a dict of currently running service APIs."""
        return self._service_api
