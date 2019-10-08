"""C callbacks to be provided to Rust"""

from typing import List, Any, Dict
import ctypes as c

from .raw_types import (
    RawArtifactId,
    RawInstanceDescriptor,
    RawInstanceSpec,
    RawCallInfo,
    RawStateHashAggregator,
    RawArtifactProtobufSpec,
    RawPythonMethods,
    RawExecutionContext,
    RawIndexAccess,
)
from .ffi_provider import RustFFIProvider

from exonum_runtime.runtime.types import PythonRuntimeResult

# Dynamically allocated resources
#
# Resources are freed by the rust through a `free` method call.
_RESOURCES: Dict[int, c.c_void_p] = dict()
# Resources allocated by the merkledb.
_MERKLEDB_ALLOCATED: List[Any] = list()


@c.CFUNCTYPE(c.c_uint8, RawArtifactId, c.POINTER(c.c_ubyte), c.c_uint64)
def deploy_artifact(raw_artifact, raw_data, raw_data_len):  # type: ignore # Signature is one line above.
    """Function called from Rust to indicate an artifact deploy request."""
    artifact_id = raw_artifact.into_artifact_id()

    artifact_spec = bytes(raw_data[:raw_data_len])

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().request_deploy(artifact_id, artifact_spec)

    return result.value


@c.CFUNCTYPE(c.c_bool, RawArtifactId)
def is_artifact_deployed(raw_artifact):  # type: ignore # Signature is one line above.
    """Function called from Rust to check if artifact is deployed."""
    artifact_id = raw_artifact.into_artifact_id()
    ffi = RustFFIProvider.instance()

    return ffi.runtime().is_artifact_deployed(artifact_id)


@c.CFUNCTYPE(c.c_uint8, RawInstanceSpec)
def start_service(raw_spec):  # type: ignore # Signature is one line above.
    """Function called from Rust to indicate an service start request."""
    instance_spec = raw_spec.into_instance_spec()

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().start_instance(instance_spec)

    return result.value


@c.CFUNCTYPE(c.c_uint8, RawIndexAccess, RawInstanceDescriptor, c.POINTER(c.c_uint8), c.c_uint32)
def initialize_service(access, descriptor, parameters, parameters_len):  # type: ignore # Signature is one line above.
    """Configure service instance"""
    instance_descriptor = descriptor.into_instance_descriptor()

    parameters_bytes = bytes(parameters[:parameters_len])

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().initialize_service(access, instance_descriptor, parameters_bytes)

    if isinstance(result, PythonRuntimeResult):
        return result.value

    # ServiceError
    return PythonRuntimeResult.SERVICE_ERRORS_START + result.code


@c.CFUNCTYPE(c.c_uint8, RawInstanceDescriptor)
def stop_service(descriptor):  # type: ignore # Signature is one line above.
    """Stop service instance"""
    instance_descriptor = descriptor.into_instance_descriptor()

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().stop_service(instance_descriptor)

    return result.value


@c.CFUNCTYPE(c.c_uint8, RawExecutionContext, RawCallInfo, c.POINTER(c.c_uint8), c.c_uint32)
def execute(raw_context, raw_call_info, parameters, parameters_len):  # type: ignore # Signature is one line above.
    """Execute a transaction."""
    call_info = raw_call_info.into_call_info()

    parameters_bytes = bytes(parameters[:parameters_len])

    context = raw_context.into_execution_context()

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().execute(context, call_info, parameters_bytes)

    if isinstance(result, PythonRuntimeResult):
        return result.value

    # ServiceError
    return PythonRuntimeResult.SERVICE_ERRORS_START + result.code


@c.CFUNCTYPE(None, c.c_void_p, c.POINTER(c.POINTER(RawStateHashAggregator)))
def state_hashes(access, state_hash_aggregator):  # type: ignore # Signature is one line above.
    """Function called from Rust to retrieve state hashes."""
    ffi = RustFFIProvider.instance()

    hashes = ffi.runtime().state_hashes(access)

    raw_state_hashes = RawStateHashAggregator.from_state_hash_aggregator(hashes)
    raw_state_hashes_ptr = c.pointer(raw_state_hashes)

    void_p = c.cast(raw_state_hashes_ptr, c.c_void_p)
    _RESOURCES[void_p.value] = void_p
    # _RESOURCES.add(c.cast(raw_state_hashes_ptr, c.c_void_p))

    state_hash_aggregator.content = raw_state_hashes_ptr


@c.CFUNCTYPE(None, RawArtifactId, c.POINTER(c.POINTER(RawArtifactProtobufSpec)))
def artifact_protobuf_spec(raw_artifact_id, spec_ptr):  # type: ignore # Signature is one line above.
    """Function called from Rust to retrieve artifact protobuf spec."""
    artifact_id = raw_artifact_id.into_artifact_id()

    ffi = RustFFIProvider.instance()

    spec = ffi.runtime().artifact_protobuf_spec(artifact_id)

    if spec is not None:
        raw_spec = RawArtifactProtobufSpec.from_artifact_protobuf_spec(spec)
        raw_spec_ptr = c.pointer(raw_spec)

        void_p = c.cast(raw_spec_ptr, c.c_void_p)

        _RESOURCES[void_p.value] = void_p
    else:
        raw_spec_ptr = None

    spec_ptr[0] = raw_spec_ptr


@c.CFUNCTYPE(None, c.c_void_p)
def before_commit(access):  # type: ignore # Signature is one line above.
    """Before commit callback."""
    ffi = RustFFIProvider.instance()

    ffi.runtime().before_commit(access)


@c.CFUNCTYPE(c.c_void_p, c.c_uint64)
def merkledb_allocate(length: int):  # type: ignore # Signature is one line above.
    """Request for memory allocation."""
    data = (c.c_uint8 * length)(*([0] * length))

    _MERKLEDB_ALLOCATED.append(data)

    return c.addressof(data)


@c.CFUNCTYPE(None, c.c_void_p)
def after_commit(access):  # type: ignore # Signature is one line above.
    """After commit callback."""
    ffi = RustFFIProvider.instance()

    ffi.runtime().after_commit(access)


@c.CFUNCTYPE(None, c.c_void_p)
def free_resource(resource):  # type: ignore # Signature is one line above.
    """Callback called when resource is consumed and can be freed."""

    # TODO probably not work
    # _RESOURCES.remove(resource)
    del _RESOURCES[resource]


def free_merkledb_allocated() -> None:
    """Free memory allocated by merkledb bindings."""
    _MERKLEDB_ALLOCATED.pop()


def build_callbacks() -> RawPythonMethods:
    """Returns a RawPythonMethods instance"""
    return RawPythonMethods(
        deploy_artifact=c.cast(deploy_artifact, c.c_void_p),
        is_artifact_deployed=c.cast(is_artifact_deployed, c.c_void_p),
        start_service=c.cast(start_service, c.c_void_p),
        initialize_service=c.cast(initialize_service, c.c_void_p),
        stop_service=c.cast(stop_service, c.c_void_p),
        execute=c.cast(execute, c.c_void_p),
        artifact_protobuf_spec=c.cast(artifact_protobuf_spec, c.c_void_p),
        state_hashes=c.cast(state_hashes, c.c_void_p),
        before_commit=c.cast(before_commit, c.c_void_p),
        after_commit=c.cast(after_commit, c.c_void_p),
        free_resource=c.cast(free_resource, c.c_void_p),
    )
