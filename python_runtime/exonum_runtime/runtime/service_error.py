"""Service error module"""
from enum import IntEnum


class GenericServiceError(IntEnum):
    """Enum denoting generic service errors."""

    WRONG_SERVICE_IMPLEMENTATION = 0
    MALFORMED_CONFIG = 1
    METHOD_NOT_FOUND = 2
    MALFORMED_PARAMETERS = 3


class ServiceError(Exception):
    """Base class for service errors.

    Codes for service errors must be in the 16..128 range.
    If code does not lie in that range, it will be enforced to be 128.

    Codes 0-15 is reserved for the `Service` class to describe generic
    execution errors."""

    def __init__(self, code: int) -> None:
        super().__init__("Service error")

        # We need to check that class is exactly ServiceError and not a subclass.
        # pylint: disable=unidiomatic-typecheck
        if type(self) != ServiceError and code < 16 or code > 128:
            code = 128

        self.code = code
