import unittest
from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry
from pacman.exceptions import PacmanAlreadyExistsException


class TestRoutingInfo(unittest.TestCase):
    def test_new_multicast_routing_table(self):
        key = 0xff35
        mask = 0x00ff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries = list()
        for i in range(5):
            multicast_entries.append(
                MulticastRoutingEntry(key + i, mask, proc_ids, link_ids, True))
        mrt = MulticastRoutingTable(0, 0, multicast_entries)
        self.assertEqual(mrt.x, 0)
        self.assertEqual(mrt.y, 0)

        mre = mrt.multicast_routing_entries
        for entry in mre:
            self.assertIn(entry, multicast_entries)
        self.assertEqual(len(mre), len(multicast_entries))
        for i in range(5):
            self.assertEqual(
                mrt.get_multicast_routing_entry_by_key(key + i, mask),
                multicast_entries[i])
        self.assertEqual(mrt.get_multicast_routing_entry_by_key(key + 5, mask),
                         None)
        self.assertEqual(mrt.get_multicast_routing_entry_by_key(key - 1, mask),
                         None)

    def test_new_multicast_routing_table_empty(self):
        MulticastRoutingTable(0, 0)

    def test_new_multicast_routing_table_duplicate_entry(self):
        key = 0xff35
        mask = 0x00ff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries = list()
        for i in range(5):
            multicast_entries.append(
                MulticastRoutingEntry(key + i, mask, proc_ids, link_ids, True))
        mrt = MulticastRoutingTable(0, 0, multicast_entries)
        with self.assertRaises(PacmanAlreadyExistsException):
            mrt.add_mutlicast_routing_entry(multicast_entries[0])

    def test_new_multicast_routing_table_duplicate_key(self):
        key = 0xff35
        mask = 0x00ff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries = list()
        for i in range(5):
            multicast_entries.append(
                MulticastRoutingEntry(key, mask, proc_ids, link_ids, True))
        with self.assertRaises(PacmanAlreadyExistsException):
            MulticastRoutingTable(0, 0, multicast_entries)

    def test_new_multicast_routing_tables(self):
        key = 0xff35
        mask = 0x00ff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries1 = MulticastRoutingEntry(key, mask, proc_ids,
                                                   link_ids, True)
        multicast_entries2 = MulticastRoutingEntry(key - 1, mask, proc_ids,
                                                   link_ids, True)
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
            key = 0xff35
            mask = 0x00ff
            proc_ids = list()
            link_ids = list()
            for i in range(18):
                proc_ids.append(i)
            for i in range(6):
                link_ids.append(i)
            multicast_entries1 = MulticastRoutingEntry(key, mask, proc_ids,
                                                       link_ids, True)

            multicast_entries2 = MulticastRoutingEntry(key - 1, mask, proc_ids,
                                                       link_ids, True)
            mrt = list()
            mrt.append(MulticastRoutingTable(3, 0, [multicast_entries1]))
            mrt.append(MulticastRoutingTable(3, 0, [multicast_entries2]))
            MulticastRoutingTables(mrt)


if __name__ == '__main__':
    unittest.main()