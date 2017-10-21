"""
TestRoutingInfo
"""

# pacman imports
from pacman.model.routing_tables \
    import MulticastRoutingTable, MulticastRoutingTables
from pacman.exceptions import PacmanAlreadyExistsException

# spinnmanchine imports
from spinn_machine import MulticastRoutingEntry

# general imports
import unittest


class TestRoutingTable(unittest.TestCase):
    """
    tests for the routing table object
    """
    def test_new_multicast_routing_table(self):
        """
        test that creating a multicast routing entry and adding it to the table
        works
        """
        key_combo = 0xff000
        mask = 0xff000
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries = list()
        for i in range(5):
            multicast_entries.append(
                MulticastRoutingEntry(key_combo + i, mask + i, proc_ids,
                                      link_ids, True))
        mrt = MulticastRoutingTable(0, 0, multicast_entries)
        self.assertEqual(mrt.x, 0)
        self.assertEqual(mrt.y, 0)

        mre = mrt.multicast_routing_entries
        for entry in mre:
            self.assertIn(entry, multicast_entries)
        self.assertEqual(len(mre), len(multicast_entries))
        for i in range(5):
            self.assertEqual(
                mrt.get_multicast_routing_entry_by_routing_entry_key(
                    key_combo + i, mask + i),
                multicast_entries[i])
        self.assertEqual(mrt.get_multicast_routing_entry_by_routing_entry_key(
            key_combo + 5, mask + 5), None)
        self.assertEqual(mrt.get_multicast_routing_entry_by_routing_entry_key(
            key_combo - 1, mask - 1), None)

    def test_new_multicast_routing_table_empty(self):
        """
        tests creating a basic multicast routing table
        """
        MulticastRoutingTable(0, 0)

    def test_new_multicast_routing_table_duplicate_entry(self):
        """
        test that adding multiple identical entries into a multicast table
        causes an error
        """
        key_combo = 0xff35
        mask = 0xff35
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries = list()
        for i in range(5):
            multicast_entries.append(MulticastRoutingEntry(
                key_combo + i, mask + i, proc_ids, link_ids, True))
        mrt = MulticastRoutingTable(0, 0, multicast_entries)
        with self.assertRaises(PacmanAlreadyExistsException):
            mrt.add_multicast_routing_entry(multicast_entries[0])

    def test_new_multicast_routing_table_duplicate_key_combo(self):

        key_combo = 0xff35
        mask = 0xffff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries = list()
        for i in range(5):
            multicast_entries.append(MulticastRoutingEntry(
                key_combo, mask, proc_ids, link_ids, True))
        with self.assertRaises(PacmanAlreadyExistsException):
            MulticastRoutingTable(0, 0, multicast_entries)

    def test_new_multicast_routing_tables(self):
        key_combo = 0xff35
        mask = 0xffff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries1 = MulticastRoutingEntry(
            key_combo, mask, proc_ids, link_ids, True)
        multicast_entries2 = MulticastRoutingEntry(
            key_combo - 1, mask - 1, proc_ids, link_ids, True)
        mrt = list()

        t1 = MulticastRoutingTable(0, 0, [multicast_entries1])
        t2 = MulticastRoutingTable(1, 0, [multicast_entries2])
        mrt.append(t1)
        mrt.append(t2)
        tables = MulticastRoutingTables(mrt)
        retrieved_tables = tables.routing_tables
        self.assertEqual(len(retrieved_tables), len(mrt))
        for tab in retrieved_tables:
            self.assertIn(tab, mrt)

        self.assertEqual(tables.get_routing_table_for_chip(0, 0), t1)
        self.assertEqual(tables.get_routing_table_for_chip(1, 0), t2)
        self.assertEqual(tables.get_routing_table_for_chip(2, 0), None)

    def test_new_multicast_routing_tables_empty(self):
        MulticastRoutingTables()

    def test_add_routing_table_for_duplicate_chip(self):
        with self.assertRaises(PacmanAlreadyExistsException):
            key_combo = 0xff35
            mask = 0xffff
            proc_ids = list()
            link_ids = list()
            for i in range(18):
                proc_ids.append(i)
            for i in range(6):
                link_ids.append(i)
            multicast_entries1 = MulticastRoutingEntry(
                key_combo, mask, proc_ids, link_ids, True)

            multicast_entries2 = MulticastRoutingEntry(
                key_combo - 1, mask, proc_ids, link_ids, True)
            mrt = list()
            mrt.append(MulticastRoutingTable(3, 0, [multicast_entries1]))
            mrt.append(MulticastRoutingTable(3, 0, [multicast_entries2]))
            MulticastRoutingTables(mrt)


if __name__ == '__main__':
    unittest.main()
