"""Common types for python runtime."""
from typing import NamedTuple, NewType, Tuple, List, Union
from enum import IntEnum

import ctypes as c

from exonum_runtime.crypto import Hash, PublicKey

# TODO: Redeclaration to avoid cyclic import (raw_types -> types -> raw_types).
RawIndexAccess = c.c_void_p


class PythonRuntimeResult(IntEnum):
    """Common runtime errors.
    
    0 means OK
    1-15 are reserved for Rust side of Python runtime.
    16-64 are reserved for Python side runtime.
    65-... are errors of the Services."""

    # Ok result.
    OK = 0

    # Errors emitted only by the rust part
    RUNTIME_NOT_READY = 1
    RUNTIME_DEAD = 2

    # Errors emitted by the python side
    WRONG_SPEC = 16
    SERVICE_INSTALL_FAILED = 17


class ArtifactId(NamedTuple):
    """Structure that represents an Artifacd ID."""

    runtime_id: int
    name: str


class InstanceSpec(NamedTuple):
    """Structure that represents an Instance Spec"""

    name: str
    artifact: ArtifactId


InstanceId = NewType("InstanceId", int)
MethodId = NewType("MethodId", int)


class DeploymentResult(NamedTuple):
    """Structure that represents an result of the deployment process"""

    result: PythonRuntimeResult
    artifact_id: ArtifactId


class InstanceDescriptor(NamedTuple):
    """Service Instance descriptor."""

    id: InstanceId
    name: str


class CallInfo(NamedTuple):
    """Information about service method call."""

    instance_id: InstanceId
    method_id: MethodId


class ProtoSourceFile(NamedTuple):
    """.proto file content."""

    name: str
    content: str


class ArtifactProtobufSpec(NamedTuple):
    """Proto sources of the artifact."""

    sources: List[ProtoSourceFile]


class StateHashAggregator(NamedTuple):
    """TODO"""

    # List of hashes of the root objects of the runtime information schema.
    runtime: List[Hash]
    # List of hashes of the root objects of the service instances schemas.
    instances: List[Tuple[InstanceId, List[Hash]]]


class CallerTransaction(NamedTuple):
    """TODO"""

    tx_hash: Hash
    author: PublicKey


class CallerService(NamedTuple):
    """TODO"""

    instance_id: InstanceId


class Caller(NamedTuple):
    """TODO"""

    caller: Union[CallerTransaction, CallerService]


class ExecutionContext(NamedTuple):
    """TODO"""

    access: RawIndexAccess
    caller: Caller
    interface_name: str
