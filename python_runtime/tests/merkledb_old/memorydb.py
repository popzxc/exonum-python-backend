"""TODO"""

import unittest

from runtime.merkledb_old.backends import MemoryDB


class TestMemoryDB(unittest.TestCase):
    """TODO"""

    def test_basic_operations(self) -> None:
        """TODO"""
        memory_db = MemoryDB()

        with memory_db.fork("a") as fork:
            fork.put(b"a", b"123")
            fork.put(b"b", b"345")

        with memory_db.fork("b") as fork:
            fork.put(b"c", b"123")
            fork.put(b"d", b"345")

        with memory_db.snapshot("a") as snapshot:
            self.assertEqual(snapshot.get(b"a"), b"123")
            self.assertEqual(snapshot.get(b"b"), b"345")
            self.assertIsNone(snapshot.get(b"c"))
            self.assertIsNone(snapshot.get(b"d"))

        with memory_db.snapshot("b") as snapshot:
            self.assertEqual(snapshot.get(b"c"), b"123")
            self.assertEqual(snapshot.get(b"d"), b"345")
            self.assertIsNone(snapshot.get(b"b"))
            self.assertIsNone(snapshot.get(b"a"))
