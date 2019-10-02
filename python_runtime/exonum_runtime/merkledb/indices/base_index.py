"""TODO"""
from typing import Any, no_type_check, Tuple, Dict
import functools

from ..types import Access


class IndexAccessError(Exception):
    """Error to be raised when mutable access requested without Fork."""


class _BaseIndexMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any]) -> type:  # type: ignore
        if name == "BaseIndex":
            # Proxy class, skip it.
            return super().__new__(cls, name, bases, dct)

        if BaseIndex not in bases:
            raise TypeError("Index classes should be derived from BaseIndex")

        # Wrap all the public methods into `_ensure`.
        for key in dct:
            if not key.startswith("_") and callable(dct[key]):
                dct[key] = _ensure(dct[key])

        return super().__new__(cls, name, bases, dct)


class BaseIndex(metaclass=_BaseIndexMeta):
    """Base interface to the database for indices."""

    def __init__(self, access: Access) -> None:
        self._access = access

    def ensure_access(self) -> None:
        """Raises an exception if access is expired."""
        if not self._access.valid():
            raise IndexAccessError("Access to index expired")


@no_type_check
def _ensure(method):
    """Ensures that access is still valid, raises an exception otherwise."""

    @functools.wraps(method)
    def ensure_handler(obj: BaseIndex, *args: Any, **kwargs: Any) -> Any:
        obj.ensure_access()

        return method(obj, *args, **kwargs)

    return ensure_handler
