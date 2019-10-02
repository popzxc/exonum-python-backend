"""TODO"""

import unittest

from runtime.crypto import KeyPair
from runtime.merkledb_old.backends import MemoryDB
from runtime.merkledb_old.index_owner import IndexOwner
from runtime.merkledb_old.indices import ListIndex


class TestListIndex(unittest.TestCase):
    """TODO"""

    def test_basic_operations(self) -> None:
        """TODO"""
        key_pair = KeyPair.generate()

        index_owner = IndexOwner("index", key_pair.secret_key)
        database = MemoryDB()

        list_index = ListIndex(database, index_owner, "a")

        with list_index.fork() as fork:
            fork.append(b"123")
            fork.append(b"345")
            self.assertEqual(len(fork), 2)
            self.assertEqual(fork[0], b"123")
            self.assertEqual(fork[1], b"345")

            with self.assertRaises(IndexError):
                _ = fork[2]

            del fork[0]
            self.assertEqual(len(fork), 1)
            self.assertEqual(fork[0], b"345")

            fork[0] = b"678"
            self.assertEqual(fork[0], b"678")
