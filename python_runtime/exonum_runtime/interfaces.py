"""Common interfaces for Python Runtime."""

import abc


class Named(metaclass=abc.ABCMeta):
    """Objects of `Named` subclasses can provide their name."""

    @abc.abstractmethod
    def instance_name(self) -> str:
        """Returns the name of the class instance."""
