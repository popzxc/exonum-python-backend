"""TODO"""

from .base_index import BaseIndex


class ListIndex(BaseIndex):
    def __getitem__(self, idx: int) -> bytes:
        pass

    @BaseIndex.mutable
    def __setitem__(self, idx: int, value: bytes) -> None:
        pass
