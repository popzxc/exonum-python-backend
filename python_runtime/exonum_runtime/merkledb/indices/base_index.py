"""TODO"""
from typing import Any, no_type_check, Tuple, Dict, Optional
import functools

from ..types import Access, Fork


class IndexAccessError(Exception):
    """Error to be raised when mutable access requested without Fork."""


class _BaseIndexMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any]) -> type:  # type: ignore
        if name == "BaseIndex":
            # Proxy class, skip it.
            return super().__new__(cls, name, bases, dct)

        if BaseIndex not in bases:
            raise TypeError("Index classes should be derived from BaseIndex")

        contaiter_methods = ["__len__", "__getitem__", "__setitem__", "__delitem__", "__contains__"]

        # Wrap all the public methods into `_ensure`.
        for key in dct:
            if key in contaiter_methods or (not key.startswith("_") and callable(dct[key])):
                dct[key] = BaseIndex._ensure(dct[key])

        return super().__new__(cls, name, bases, dct)


class BaseIndex(metaclass=_BaseIndexMeta):
    """Base interface to the database for indices."""

    def __init__(self, access: Access, instance_name: str, index_name: str, family: Optional[str]):
        self._access = access
        if family is None:
            self._index_id = bytes(f"{instance_name}.{index_name}", "utf-8")
        else:
            self._index_id = bytes(f"{instance_name}.{index_name}.{family}", "utf-8")

        self.initialize()

    def initialize(self) -> None:
        """Method to be overriden by children classes to perform their init."""

    def ensure_access(self) -> None:
        """Raises an exception if access is expired."""
        if not self._access.valid():
            raise IndexAccessError("Access to index expired")

    @no_type_check
    @staticmethod
    def mutable(method):
        """Ensures that type of access is Fork."""

        @functools.wraps(method)
        def ensure_fork(obj: BaseIndex, *args: Any, **kwargs: Any) -> Any:
            # pylint: disable=protected-access
            if not isinstance(obj._access, Fork):
                raise IndexAccessError("Attemt to get mutable access with a Snapshot")

            return method(obj, *args, **kwargs)

        return ensure_fork

    @no_type_check
    @staticmethod
    def _ensure(method):
        """Ensures that access is still valid, raises an exception otherwise."""

        @functools.wraps(method)
        def ensure_handler(obj: BaseIndex, *args: Any, **kwargs: Any) -> Any:
            obj.ensure_access()

            return method(obj, *args, **kwargs)

        return ensure_handler
