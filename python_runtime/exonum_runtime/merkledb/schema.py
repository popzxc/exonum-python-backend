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
        """This method does not mutate the class, it's only performing all required checks:

        - Class should be directly derived from `WithSchema`;
        - Class should have `Named` in the type hierarchy;
        - Class should provide `_schema` attribute and it should point to the class derived from `Schema`;
        - Class should provide `_state_hash_` attribute and it shoul contain names of Proof*Index indices
          from the schema. If there is no state hash for class, this attribute should be an empty list.
        """
        if name == "WithSchema":
            # Proxy class, skip it.
            return super().__new__(  # type: ignore  # mypy doesn't see ABCMeta signature
                cls, name, bases, dct, **kwargs
            )

        # Check that class is derived from `WithSchema`.
        cls._verify_cls_derived_from_with_schema(bases)

        # Check that class is subclass of `Named`.
        cls._verify_named_in_bases(bases)

        # Check that _schema_ attribute is set.
        schema = dct.get("_schema_")
        cls._verify_schema_attr(schema)
        assert schema is not None

        # Check that if _state_hash_ attribute is set, it has correct layout.
        state_hash = dct.get("_state_hash_")
        cls._verify_state_hash_attr(schema, state_hash)

        new_class = super().__new__(cls, name, bases, dct, **kwargs)  # type: ignore
        return new_class

    @staticmethod
    def _incorrect_schema_attribute_error() -> AttributeError:
        message = "_schema_ variable must be a list of pairs, e.g. [('wallets', ProofListIndex)]"

        return AttributeError(message)

    @staticmethod
    def _verify_cls_derived_from_with_schema(bases: Tuple[type, ...]) -> None:
        """Verifies that class directly inhetrits WithSchema"""
        if WithSchema not in bases:
            raise TypeError("Classes with schema should be directly derived from WithSchema class")

    @staticmethod
    def _verify_named_in_bases(bases: Tuple[type, ...]) -> None:
        """Verifies that Named class is in the type hierarchy."""
        # To check it we check if any of class bases is subclass of `Named`.
        if not any(map(lambda t: issubclass(t, Named), bases)):
            raise TypeError("Classes with schema should be subclasses of `Named` class")

    @classmethod
    def _verify_schema_attr(cls, schema: Optional[type]) -> None:
        """Verifies that _schema_ attribute is a subclass of Schema"""
        if schema is None or not issubclass(schema, Schema):
            raise cls._incorrect_schema_attribute_error()

    @staticmethod
    def _verify_state_hash_attr(schema: Dict[str, Any], state_hash: Optional[Dict[str, Any]]) -> None:
        """Verifies that state hash attribute is a list of schema index names
        and every element in that list points to Proof*Index."""

        if state_hash is None:
            raise AttributeError(
                "_state_hash_ attribute must be a list of strings. If you don't need state hash, use empty list"
            )

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


class WithSchema(metaclass=_WithSchemaMeta):
    """Base class for classes that do work with database.

    Classes derived from `WithSchema` should also inherit `Named` (directly or indirectly).

    Also class should define two class attributes:

    _schema_ -- a type derived from Schema, for example:

    >>> _schema_ = SomeSchema

    _state_hash_ -- a list of index names from which state hash should be calculated,
    for example:

    >>> _state_hash_ = ["wallets"]

    Please note that provided names should persist in schema passed to the _schema_ attribute
    and point to `Proof*Index` type. Otherwise an exception will be raised.

    If no state hash should be calculated for class, `_state_hash_` should be an empty list.
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

        if not self._state_hash_:
            # No state hash should be calculated, return an empty list without creating schema.
            return []

        # _schema_ is type, it's callable (see check above)
        # pylint: disable=not-callable
        schema = self._schema_(self, access)

        # _state_hash_ is a list, it's an iterable (see check above)
        # pylint: disable=not-an-iterable
        for index_name in self._state_hash_:
            index: Union[ProofListIndex, ProofMapIndex] = getattr(schema, index_name)()

            state_hashes.append(index.object_hash())

        return state_hashes

    @classmethod
    def schema(cls, owner: Union[Named, str], access: Access) -> "Schema":
        """Gets the Schema assotiated with that service."""
        assert cls._schema_ is not None, "Attempt to call `schema()` on class without schema"

        # pylint: disable=not-callable
        return cls._schema_(owner, access)


class _SchemaMeta(abc.ABCMeta):
    """Metaclass for Schema class.

    It parses type annotations defined in the class body
    and initialized metadata.
    """

    def __new__(cls, name: str, bases: Tuple[type, ...], dct: Dict[str, Any], **kwargs: Any) -> type:  # type: ignore
        """This method performs required checks and fills the "_schema_meta" attribute with
        mapping `index name` => `index type`.

        Performed checks:

        - Class should directly inherit `Schema`;
        - Class should provide type annotations to define used indices;
        - Indices types should be inherited from `BaseIndex`.
        """
        if name == "Schema":
            # Proxy class, skip it.
            return super().__new__(  # type: ignore  # mypy doesn't see ABCMeta signature
                cls, name, bases, dct, **kwargs
            )

        # Check that class is derived from `Schema`.
        cls._verify_schema_in_bases(bases)

        # Check that class have type annotations and get them.
        annotations = cls._get_annotations(dct)

        # Fill the schema metainformation
        dct["_schema_meta"] = dict()

        for index_name, index_type in annotations.items():
            # Check that index type is subclass of `BaseIndex`.
            if not issubclass(index_type, BaseIndex):
                raise AttributeError(f"Incorrect index type: {index_type}")

            dct["_schema_meta"][index_name] = index_type

        new_class = super().__new__(cls, name, bases, dct, **kwargs)  # type: ignore
        return new_class

    @staticmethod
    def _verify_schema_in_bases(bases: Tuple[type, ...]) -> None:
        if Schema not in bases:
            raise TypeError("Schemas should be derived from Schema class")

    @staticmethod
    def _get_annotations(dct: Dict[str, Any]) -> Dict[str, Any]:
        annotations = dct.get("__annotations__")

        if annotations is None:
            # Empty schema
            return dict()

        return annotations


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

    Please note that this class overrides `__getattribute__` method to provide
    handy interface of interaction with schema, so user-defined schemas should
    not override it.
    """

    @classmethod
    def indices(cls) -> List[str]:
        """Returns list of the indices names from the schema."""

        return getattr(cls, "_schema_meta").keys()

    @classmethod
    def index_type(cls, index_name: str) -> type:
        """Returns the type of the index with provided name."""

        return getattr(cls, "_schema_meta")[index_name]

    def __init__(self, owner: Union[Named, str], access: Access):
        self._access = access
        if isinstance(owner, Named):
            self._owner = owner.instance_name()
        elif isinstance(owner, str):
            self._owner = owner
        else:
            raise ValueError(f"Owner must be either an instance of Named or string, but got {owner}")

    def __getattribute__(self, name: str) -> Any:
        schema_meta = super().__getattribute__("_schema_meta")
        if name in schema_meta:
            # If we're accessing the name assotiated with index,
            # create an object of that index and return it.
            index_type = schema_meta[name]

            instance_name = self._owner
            index_name = name

            return index_type(self._access, instance_name, index_name)

        return super().__getattribute__(name)
