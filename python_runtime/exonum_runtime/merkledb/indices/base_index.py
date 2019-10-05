"""TODO"""
from typing import Any, no_type_check, Tuple, Dict, Optional, Union, Type
import functools

from ..types import Access, Fork
from ..into_bytes import IntoBytes


class IndexAccessError(Exception):
    """Error to be raised when mutable access requested without Fork."""


IndexDataTypes = Union[Type[IntoBytes], Tuple[Type[IntoBytes], Type[IntoBytes]]]
# Pool of generated typed classes to avoid re-creation.
_descriptor_pool: Dict[Tuple[type, IndexDataTypes], "_BaseIndexMeta"] = dict()


class _BaseIndexMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any]) -> type:  # type: ignore
        if name == "BaseIndex":
            # Proxy class, skip it.
            return super().__new__(cls, name, bases, dct)

        if BaseIndex not in bases:
            raise TypeError("Index classes should be derived from BaseIndex")

        # Methods that don't need an `ensure` check
        skip_methods = ["initialize", "ensure_access", "mutable"]

        # Containter methods should be wrapped.
        contaiter_methods = ["__len__", "__getitem__", "__setitem__", "__delitem__", "__contains__", "__iter__"]

        # Wrap all the public methods into `_ensure`.
        for key in dct:
            if key in skip_methods:
                continue

            if key in contaiter_methods or (not key.startswith("_") and callable(dct[key])):
                dct[key] = BaseIndex._ensure(dct[key])

        return super().__new__(cls, name, bases, dct)

    def __getitem__(cls, item: IndexDataTypes) -> type:
        """Instatiation of generic types of stored types.

        For example, having two classes `SomeKey` and `SomeValue` which are subclasses of
        `IntoBytes`, the following code:

        >>> ListIndex[SomeValue]
        >>> MapIndex[SomeKey, SomeValue]

        will be resolved into concrete Index types which know the types of data stored inside.

        With this information, indices will be able to serialize/deserialize data correctly.
        """

        # Check if we've instatiated this type before
        if (cls, item) in _descriptor_pool:
            return _descriptor_pool[(cls, item)]

        one_generic = isinstance(item, type)
        two_generics = (
            isinstance(item, tuple)
            and len(item) == 2
            and issubclass(item[0], IntoBytes)
            and issubclass(item[1], IntoBytes)
        )

        if not (one_generic or two_generics):
            raise ValueError("Key/value types in indices must be subclasses of IntoBytes")

        dct = dict(cls.__dict__)
        bases = cls.__bases__
        name = cls.__name__

        dct["_generic"] = item

        # Create a new class with instatiated generic types
        new_class = super().__new__(type(cls), name, bases, dct)

        # Store it into descriptor cache
        _descriptor_pool[(cls, item)] = new_class  # type: ignore

        return new_class

    def _one_index_type(cls) -> Type[IntoBytes]:
        """Gets the concrete types for data stored in indices.

        Raises an RuntimeError if it was attempted to initalize an Index
        with generic types."""
        # Check that there is only one generic type and it's a subclass of IntoBytes.
        if not hasattr(cls, "_generic") or not issubclass(getattr(cls, "_generic"), IntoBytes):
            raise RuntimeError(
                "You must specify key type, e.g. ListIndex[Type], where SomeType is subclass of IntoBytes"
            )

        # If we've reached this point, all the checks are passed and concrete type may be returned.
        return getattr(cls, "_generic")

    def _two_index_types(cls) -> Tuple[Type[IntoBytes], Type[IntoBytes]]:
        """Gets the concrete types for data stored in indices.

        Raises an RuntimeError if it was attempted to initalize an Index
        with generic types."""

        failure = False
        # Check that we have "_generic" attribute set
        if not hasattr(cls, "_generic"):
            failure = True
        else:
            # Check that "_generic" is a tuple of two subclasses of IntoBytes.
            item = getattr(cls, "_generic")
            failure = not (
                isinstance(item, tuple)
                and len(item) == 2
                and issubclass(item[0], IntoBytes)
                and issubclass(item[1], IntoBytes)
            )

        if failure:
            raise RuntimeError(
                "You must specify key type, e.g. MapIndex[Type, Type], where Type is subclass of IntoBytes"
            )

        # If we've reached this point, all the checks are passed and concrete types may be returned.
        return getattr(cls, "_generic")


class BaseIndex(metaclass=_BaseIndexMeta):
    """Base interface to the database for indices.

    Example of usage:

    >>> some_index_generic = SomeIndex(access, "instance", "index")
    >>> some_index = some_index_generic("family_123")
    >>> some_index.concrete_index_operation()

    That may look a bit complicated (why call the index twice?), but this is required
    to make `Schema` class comfortable.
    """

    def __init__(self, access: Access, instance_name: str, index_name: str):
        self._access = access
        self._instance_name = instance_name
        self._index_name = index_name
        self._index_id = b""

        self._initialized = False

    def __call__(self, family: Optional[str]) -> "BaseIndex":
        """Initializes the index and sets the index family if provided."""
        if family is None:
            self._index_id = bytes(f"{self._instance_name}.{self._index_name}", "utf-8")
        else:
            self._index_id = bytes(f"{self._instance_name}.{self._index_name}.{family}", "utf-8")

        self.initialize()

        self._initialized = True

        return self

    def initialize(self) -> None:
        """Method to be overriden by children classes to perform their init."""

    def ensure_access(self) -> None:
        """Raises an exception if access is expired or attempted to access
        not initialized index."""
        if not self._initialized:
            raise IndexAccessError(
                "Service is initialized. See the `BaseIndex` docs to check if you're creating objects correctly"
            )

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
