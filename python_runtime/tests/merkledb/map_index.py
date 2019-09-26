"""TODO"""

import unittest

from runtime.crypto import KeyPair
from runtime.merkledb.backends import MemoryDB
from runtime.merkledb.index_owner import IndexOwner
from runtime.merkledb.indices import MapIndex


class TestMapIndex(unittest.TestCase):
    """TODO"""

    def test_basic_operations(self) -> None:
        """TODO"""
        key_pair = KeyPair.generate()

        index_owner = IndexOwner("index", key_pair.secret_key)
        database = MemoryDB()

        map_index = MapIndex(database, index_owner, "a")

        with map_index.fork() as fork:
            fork[b"123"] = b"345"
            fork[b"456"] = b"678"
            self.assertEqual(fork[b"123"], b"345")
            self.assertEqual(fork[b"456"], b"678")

