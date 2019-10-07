"""TODO"""
try:
    from .runtime_pb2 import PythonArtifactSpec as ProtoPythonArtifactSpec
    from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError
except (ModuleNotFoundError, ImportError):
    raise RuntimeError(".proto files are not generated or protobuf library is not installed")

from typing import NamedTuple

from exonum_runtime.crypto import Hash


def _attempt_parse(obj: ProtobufMessage, data: bytes) -> None:
    try:
        obj.ParseFromString(data)
    except ProtobufDecodeError:
        raise ParseError("Incorrect protobuf message")


class ParseError(Exception):
    """Error to be raised on protobuf decode error."""


class PythonArtifactSpec(NamedTuple):
    """Python artifact metadata."""

    source_wheel_name: str
    service_library_name: str
    service_class_name: str
    expected_hash: Hash

    # Pylint doesn't see protobuf-generated structure.
    # pylint: disable=no-member
    @classmethod
    def from_bytes(cls, data: bytes) -> "PythonArtifactSpec":
        """Atempts to parse a PythonArtifactSpec object from bytes."""

        python_spec = ProtoPythonArtifactSpec()
        _attempt_parse(python_spec, data)

        source_wheel_name = python_spec.source_wheel_name
        service_library_name = python_spec.service_library_name
        service_class_name = python_spec.service_class_name

        try:
            expected_hash = Hash(python_spec.hash)
        except ValueError:
            raise ParseError("Incorrect hash value")

        return PythonArtifactSpec(source_wheel_name, service_library_name, service_class_name, expected_hash)
