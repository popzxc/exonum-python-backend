"""C callbacks to be provided to Rust"""

from typing import Set, List, Any
import ctypes as c

from .raw_types import (
    RawArtifactId,
    RawInstanceDescriptor,
    RawInstanceSpec,
    RawCallInfo,
    RawStateHashAggregator,
    RawArtifactProtobufSpec,
    RawPythonMethods,
)
from .ffi import RustFFIProvider

# Dynamically allocated resources
#
# Resources are freed by the rust through a `free` method call.
_RESOURCES: Set[c.c_void_p] = set()
# Resources allocated by the merkledb.
_MERKLEDB_ALLOCATED: List[Any] = list()


@c.CFUNCTYPE(c.c_bool, RawArtifactId, c.POINTER(c.c_ubyte), c.c_uint64)
def deploy_artifact(raw_artifact, raw_data, raw_data_len):  # type: ignore # Signature is one line above.
    """Function called from Rust to indicate an artifact deploy request."""
    artifact_id = raw_artifact.into_artifact_id()

    artifact_spec = bytes((c.c_ubyte * raw_data_len.value).from_buffer(raw_data)[:])

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().request_deploy(artifact_id, artifact_spec)

    return result.value


@c.CFUNCTYPE(c.c_bool, RawArtifactId)
def is_artifact_deployed(raw_artifact):  # type: ignore # Signature is one line above.
    """Function called from Rust to check if artifact is deployed."""
    artifact_id = raw_artifact.into_artifact_id()
    ffi = RustFFIProvider.instance()

    return ffi.runtime().is_artifact_deployed(artifact_id)


@c.CFUNCTYPE(c.c_uint32, RawInstanceSpec)
def start_service(raw_spec):  # type: ignore # Signature is one line above.
    """Function called from Rust to indicate an service start request."""
    instance_spec = raw_spec.into_instance_spec()

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().start_service(instance_spec)

    return result.result.value


@c.CFUNCTYPE(c.c_uint32, RawInstanceDescriptor, c.POINTER(c.c_uint8), c.c_uint32)
def initialize_service(descriptor, parameters, parameters_len):  # type: ignore # Signature is one line above.
    """Configure service instance"""
    instance_descriptor = descriptor.into_instance_descriptor()

    parameters_bytes = bytes((c.c_ubyte * parameters_len.value).from_buffer(parameters)[:])

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().initialize_service(instance_descriptor, parameters_bytes)

    return result.value


@c.CFUNCTYPE(c.c_uint32, RawInstanceDescriptor)
def stop_service(descriptor):  # type: ignore # Signature is one line above.
    """Stop service instance"""
    instance_descriptor = descriptor.into_instance_descriptor()

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().stop_service(instance_descriptor)

    return result.value


@c.CFUNCTYPE(c.c_uint32, RawCallInfo, c.POINTER(c.c_uint8), c.c_uint32)
def execute(raw_call_info, parameters, parameters_len):  # type: ignore # Signature is one line above.
    """Execute a transaction."""
    call_info = raw_call_info.into_call_info()

    parameters_bytes = bytes((c.c_ubyte * parameters_len.value).from_buffer(parameters)[:])

    ffi = RustFFIProvider.instance()

    result = ffi.runtime().execute(call_info, parameters_bytes)

    return result.value


@c.CFUNCTYPE(None, c.POINTER(c.POINTER(RawStateHashAggregator)))
def state_hashes(state_hash_aggregator):  # type: ignore # Signature is one line above.
    """Function called from Rust to retrieve state hashes."""
    ffi = RustFFIProvider.instance()

    hashes = ffi.runtime().state_hashes()

    raw_state_hashes = RawStateHashAggregator.from_state_hash_aggregator(hashes)
    raw_state_hashes_ptr = c.pointer(raw_state_hashes)

    _RESOURCES.add(c.cast(raw_state_hashes_ptr, c.c_void_p))

    state_hash_aggregator.content = raw_state_hashes_ptr


@c.CFUNCTYPE(None, RawArtifactId, c.POINTER(c.POINTER(RawArtifactProtobufSpec)))
def artifact_protobuf_spec(raw_artifact_id, spec):  # type: ignore # Signature is one line above.
    """Function called from Rust to retrieve artifact protobuf spec."""
    artifact_id = raw_artifact_id.into_artifact_id()

    ffi = RustFFIProvider.instance()

    spec = ffi.runtime().artifact_protobuf_spec(artifact_id)

    if spec is not None:
        raw_spec = RawArtifactProtobufSpec.from_artifact_protobuf_spec(spec)
        raw_spec_ptr = c.pointer(raw_spec)

        _RESOURCES.add(c.cast(raw_spec_ptr, c.c_void_p))
    else:
        raw_spec_ptr = None

    spec.content = raw_spec_ptr


@c.CFUNCTYPE(None)
def before_commit():  # type: ignore # Signature is one line above.
    """Before commit callback."""
    ffi = RustFFIProvider.instance()

    ffi.runtime().before_commit()


@c.CFUNCTYPE(c.c_void_p, c.c_uint64)
def merkledb_allocate(length: int):  # type: ignore # Signature is one line above.
    """Request for memory allocation."""
    data = (c.c_uint8 * length)(*([0] * length))

    _MERKLEDB_ALLOCATED.append(data)

    return c.addressof(data)


@c.CFUNCTYPE(None, c.c_void_p)
def after_commit(_fork):  # type: ignore # Signature is one line above.
    """After commit callback."""
    ffi = RustFFIProvider.instance()

    # TODO fix call
    ffi.runtime().after_commit()


@c.CFUNCTYPE(None, c.c_void_p)
def free_resource(resource):  # type: ignore # Signature is one line above.
    """Callback called when resource is consumed and can be freed."""

    # TODO probably not work
    _RESOURCES.remove(resource)


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