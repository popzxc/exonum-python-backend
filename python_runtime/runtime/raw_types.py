"""C representation of Python types."""

from typing import List, Tuple, Any
import ctypes as c

from .types import ArtifactId, InstanceSpec, StateHashAggregator, ArtifactProtobufSpec, InstanceDescriptor, CallInfo
from .crypto import Hash


class RawPythonMethods(c.Structure):
    _fields_ = [
        ("deploy_artifact", c.c_void_p),
        ("is_artifact_deployed", c.c_void_p),
        ("start_service", c.c_void_p),
        ("configure_service", c.c_void_p),
        ("stop_service", c.c_void_p),
        ("execute", c.c_void_p),
        ("artifact_protobuf_spec", c.c_void_p),
        ("state_hashes", c.c_void_p),
        ("before_commit", c.c_void_p),
        ("after_commit", c.c_void_p),
        ("free_resource", c.c_void_p),
    ]


class RawArtifactId(c.Structure):
    """C representation of ArtifactId used in communication between Python and Rust."""

    _fields_ = [("runtime_id", c.c_uint32), ("name", c.c_char_p)]

    def into_artifact_id(self) -> ArtifactId:
        """Converts c-like artifact id into python-friendly form."""
        runtime_id = int(self.runtime_id)
        name = str(c.string_at(self.name), "utf-8")

        return ArtifactId(runtime_id, name)

    @classmethod
    def from_artifact_id(cls, artifact_id: ArtifactId) -> "RawArtifactId":
        """Converts python version of ArtifactID into c-compatible."""
        return cls(runtime_id=artifact_id.runtime_id, name=artifact_id.name)


class RawInstanceSpec(c.Structure):
    """C representation of InstanceSpec used in communication between Python and Rust."""

    _fields_ = [("name", c.c_char_p), ("artifact", RawArtifactId)]

    def into_instance_spec(self) -> InstanceSpec:
        """Converts c-like artifact id into python-friendly form."""
        name = str(c.string_at(self.name), "utf-8")
        artifact_id = self.artifact.into_artifact_id()

        return InstanceSpec(name, artifact_id)

    @classmethod
    def from_instance_spec(cls, instance_spec: InstanceSpec) -> "RawInstanceSpec":
        """Converts python version of ArtifactID into c-compatible."""
        raw_artifact = RawArtifactId.from_artifact_id(instance_spec.artifact)
        return cls(name=instance_spec.name, artifact=raw_artifact)


class RawInstanceDescriptor(c.Structure):
    """Instance descriptor."""

    _fields_ = [("id", c.c_uint32), ("name", c.c_char_p)]

    def into_instance_descriptor(self) -> InstanceDescriptor:
        """Converts c-like artifact id into python-friendly form."""
        name = str(c.string_at(self.name), "utf-8")
        instance_id = self.instance_id

        return InstanceDescriptor(id=instance_id, name=name)


class RawCallInfo(c.Structure):
    """Call info"""

    _fields_ = [("instance_id", c.c_uint32), ("method_id", c.c_uint32)]

    def into_call_info(self) -> CallInfo:
        """Converts to CallInfo"""
        return CallInfo(instance_id=self.instance_id, method_id=self.method_id)


class RawHash(c.Structure):
    """C representation of the hash."""

    _fields_ = [("data", c.c_uint8 * 32)]

    @classmethod
    def from_hash(cls, value: Hash) -> "RawHash":
        """Converts Hash to RawHash."""
        hash_data = (c.c_uint8 * 32)(*value.value)

        return cls(data=hash_data)


class RawStateHashAggregator(c.Structure):
    """C representation of StateHashAggregator.

    This structure contain an array of pointers, and every single one of those
    points to an array of `RawHash` data.
    The second field is a pointer to an array of arrays lengths.
    The third field is a pointer to an array of `InstanceId`s denoting the ownership of hashes
    in the first argument.
    The fourth field is amount of items in the second field.

    Amount of items in the third field is (fourth field) - 1, because first array from the first
    field is the runtime hashes.
    """

    _fields_ = [
        ("hashes", c.POINTER(c.POINTER(RawHash))),
        ("hashes_length", c.POINTER(c.c_uint32)),
        ("instance_ids", c.POINTER(c.c_uint32)),
        ("length", c.c_uint32),
    ]

    @classmethod
    def from_state_hash_aggregator(cls, aggregator: StateHashAggregator) -> "RawStateHashAggregator":
        """Creates RawStateHashAggregator from python type."""

        def to_raw_hashes(hashes: List[Hash]) -> Tuple[Any, c.c_uint32]:
            length = len(hashes)

            raw_hashes = (RawHash * length)(*list(map(RawHash.from_hash, hashes)))

            return (raw_hashes, c.c_uint32(length))

        instances_amount = len(aggregator.instances)
        overall_amount = instances_amount + 1

        hashes_array = []
        length_array = []
        instance_ids_array = []

        runtime_hashes, runtime_length = to_raw_hashes(aggregator.runtime)

        hashes_array.append(runtime_hashes)
        length_array.append(runtime_length)

        for instance_id, hashes in aggregator.instances:
            instance_hashes, instance_length = to_raw_hashes(hashes)

            hashes_array.append(instance_hashes)
            length_array.append(instance_length)

            instance_ids_array.append(instance_id)

        raw_hashes_array = (c.POINTER(RawHash) * overall_amount)(*hashes_array)
        raw_length_array = (c.c_uint32 * overall_amount)(*length_array)
        raw_instance_ids_array = (c.c_uint32 * instances_amount)(*instance_ids_array)

        # TODO is pointer required here?
        return cls(
            hashes=raw_hashes_array,
            hashes_length=raw_length_array,
            instance_ids=raw_instance_ids_array,
            length=overall_amount,
        )


class RawProtoSourceFile(c.Structure):
    """C representation of Proto Source file."""

    _fields_ = [("name", c.c_char_p), ("content", c.c_char_p)]


class RawArtifactProtobufSpec(c.Structure):
    """C representation of ArtifactProtobufSpec."""

    _fields_ = [("files", c.POINTER(RawProtoSourceFile)), ("files_amount", c.c_uint32)]

    @classmethod
    def from_artifact_protobuf_spec(cls, spec: ArtifactProtobufSpec) -> "RawArtifactProtobufSpec":
        """Converts ArtifactProtobufSpec into C representation."""

        files_iter = map(lambda f: RawProtoSourceFile(name=f.name, content=f.content), spec.sources)
        raw_files = (RawProtoSourceFile * len(spec.sources))(*list(files_iter))

        return cls(files=raw_files, files_amount=len(spec.sources))
