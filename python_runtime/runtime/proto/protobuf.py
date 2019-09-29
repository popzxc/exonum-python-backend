"""TODO"""
try:
    from .runtime_pb2 import PythonArtifactSpec as ProtoPythonArtifactSpec
    from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError
except (ModuleNotFoundError, ImportError):
    raise RuntimeError(".proto files are not generated or protobuf library is not installed")

from typing import NamedTuple

from python_runtime.runtime.crypto import Hash


def _attempt_parse(obj: ProtobufMessage, data: bytes) -> None:
    try:
        obj.ParseFromString(data)
    except ProtobufDecodeError:
        raise ParseError()


class ParseError(Exception):
    """Error to be raised on protobuf decode error."""


class PythonArtifactSpec(NamedTuple):
    """Python artifact metadata."""

    expected_hash: Hash

    @classmethod
    def from_bytes(cls, data: bytes) -> "PythonArtifactSpec":
        """Atempts to parse a PythonArtifactSpec object from bytes."""

        python_spec = ProtoPythonArtifactSpec()
        _attempt_parse(python_spec, data)

        return python_spec
