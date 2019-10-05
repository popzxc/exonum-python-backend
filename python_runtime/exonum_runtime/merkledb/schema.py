"""TODO"""

import abc
from typing import Tuple, Dict, Any, List, Optional, Type, Union

from exonum_runtime.crypto import Hash
from exonum_runtime.interfaces import Named
from .indices.base_index import BaseIndex
from .indices import ProofListIndex, ProofMapIndex
from .types import Access


class _WithSchemaMeta(abc.ABCMeta):
    """Metaclass for objects that do have schema.

    It parses _schema_ and _state_hash_ attributes of the class
    and verifies them.
    """

    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any], **kwargs: Any) -> type:  # type: ignore
        if name == "WithSchema":
            # Proxy class, skip it.
            return super().__new__(  # type: ignore  # mypy doesn't see ABCMeta signature
                cls, name, bases, dct, **kwargs
            )

        # TODO refactor code below to be more readable

        # Check that class is derived from `WithSchema`.
        if WithSchema not in bases:
            raise TypeError("Classes with schema should be derived from WithSchema class")

        # Check that class is subclass of `Named`.
        # To check it we check if any of class bases is subclass of `Named`.
        if not any(map(lambda t: issubclass(t, Named), bases)):
            raise TypeError("Classes with schema should be subclasses of `Named` class")

        # Check that _schema_ attribute is set.
        schema = dct.get("_schema_")
        if schema is None or not issubclass(schema, Schema):
            raise cls._incorrect_schema_attribute_error()

        # Check that if _state_hash_ attribute is set, it has correct layout.
        state_hash = dct.get("_state_hash_")
        if state_hash is not None:
            if not isinstance(state_hash, list):
                raise AttributeError("_state_hash_ attribute must be a list of strings")

            for item in state_hash:
                if not isinstance(item, str):
                    raise AttributeError("_state_hash_ attribute must be a list of strings")

                # Indices from _state_hash_ should be names from _schema_
                if getattr(schema, "_schema_meta").get(item) is None:
                    raise AttributeError(f"Item '{item}' is not a part of defined _schema_")

                if getattr(schema, "_schema_meta")[item] not in (ProofListIndex, ProofMapIndex):
                    raise AttributeError(f"Item '{item}' is not a Proof*Index")

        if "__getattr__" in dct:
            raise AttributeError("Classes derived from `WithSchema` should not implement __getattr__")

        new_class = super().__new__(cls, name, bases, dct, **kwargs)  # type: ignore
        return new_class

    @staticmethod
    def _incorrect_schema_attribute_error() -> AttributeError:
        message = "_schema_ variable must be a list of pairs, e.g. [('wallets', ProofListIndex)]"

        return AttributeError(message)


class WithSchema(metaclass=_WithSchemaMeta):
    """Base class for classes that do work with database.

    Classes derived from `WithSchema` should define two class
    attributes:

    _schema_ -- a type derived from Schema, for example:

    >>> _schema_ = SomeSchema

    _state_hash_ -- a list of index names from which state hash should be calculated,
    for example:

    >>> _state_hash_ = ["wallets"]

    Please note that provided names should persist in schema passed to the _schema_ attribute
    and point to `Proof*Index` type. Otherwise an exception will be raised.
    """

    _schema_: Optional[Type["Schema"]] = None
    _state_hash_: Optional[List[str]] = None

    def _get_indices(self) -> List[str]:
        return getattr(self, "_schema_meta").values()

    def get_state_hashes(self, access: Access) -> List[Hash]:
        """Returns a list of state hashes from indices defined in _state_hash_ attribute."""
        state_hashes: List[Hash] = []

        # Assertions to give static analysis tools hints of invariants.
        assert self._schema_ is not None
        assert issubclass(self._schema_, Schema)
        assert isinstance(self._state_hash_, list)
        assert isinstance(self, Named)

        # _schema_ is type, it's callable (see check above)
        # pylint: disable=not-callable
        schema = self._schema_(self, access)

        # _state_hash_ is a list, it's an iterable (see check above)
        # pylint: disable=not-an-iterable
        for index_name in self._state_hash_:
            index: Union[ProofListIndex, ProofMapIndex] = getattr(schema, index_name)()

            state_hashes.append(index.object_hash())

        return state_hashes


class _SchemaMeta(abc.ABCMeta):
    """Metaclass for Schema class.

    It parses type annotations defined in the class body
    and initialized metadata.
    """

    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any], **kwargs: Any) -> type:  # type: ignore
        if name == "Schema":
            # Proxy class, skip it.
            return super().__new__(  # type: ignore  # mypy doesn't see ABCMeta signature
                cls, name, bases, dct, **kwargs
            )

        # Check that class is derived from `Schema`.
        if Schema not in bases:
            raise TypeError("Schemas should be derived from Schema class")

        annotations = dct.get("__annotations__")

        if annotations is None:
            raise AttributeError("Schema must provide information about used indices")

        dct["_schema_meta"] = dict()

        for index_name, index_type in annotations.items():
            if not issubclass(index_type, BaseIndex):
                raise AttributeError(f"Incorrect index type: {index_type}")

            dct["_schema_meta"][index_name] = index_type

        new_class = super().__new__(cls, name, bases, dct, **kwargs)  # type: ignore
        return new_class


class Schema(metaclass=_SchemaMeta):
    """Base class for user-defined Schemas.

    It should provide indices names and types.

    Example:

    >>> class CurrencySchema(Schema):
    ...     wallets: ProofMapIndex
    ...     some_data: ListIndex

    Then created schema can be used in the class derived from `WithSchema`:

    >>> class SchemaUser(WithSchema):
    ...     _schema_ = CurrencySchema
    ...     _state_hash_ = ["wallets"]
    """

    @classmethod
    def indices(cls) -> List[str]:
        """Returns list of the indices names from the schema."""

        return getattr(cls, "_schema_meta").keys()

    @classmethod
    def index_type(cls, index_name: str) -> type:
        """Returns the type of the index with provided name."""

        return getattr(cls, "_schema_meta")[index_name]

    def __init__(self, owner: Named, access: Access):
        self._access = access
        self._owner = owner

    def __getattribute__(self, name: str) -> Any:
        schema_meta = super().__getattribute__("_schema_meta")
        if name in schema_meta:
            # If we're accessing the name assotiated with index,
            # create an object of that index and return it.
            index_type = schema_meta[name]

            instance_name = self._owner.instance_name()
            index_name = name

            return index_type(self._access, instance_name, index_name)

        return super().__getattribute__(name)
