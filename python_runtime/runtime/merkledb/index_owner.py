"""TODO"""
from runtime.crypto import SecretKey, Signature


class IndexOwner:
    """TODO"""

    def __init__(self, name: str, key: SecretKey):
        self._prefix = Signature.sign(bytes(name, "utf-8"), key).hex()

    def into_index_name(self, name: str) -> str:
        """TODO"""
        return f"{self._prefix}_{name}"
