# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from pacman.config_setup import unittest_setup
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.model.routing_tables.multicast_routing_tables import (
    to_json, from_json)
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman.utilities import file_format_schemas
from pacman.model.graphs.machine import SimpleMachineVertex


class TestRoutingTable(unittest.TestCase):
    """
    tests for the routing table object
    """

    def setUp(self):
        unittest_setup()

    def test_new_multicast_routing_table_entry(self):
        """
        test that creating a multicast routing entry works
        """
        # TODO: Move this test to SpiNNMachine's test suite
        key_combo = 0xff00
        mask = 0xff00
        proc_ids = range(18)
        link_ids = range(6)
        MulticastRoutingEntry(key_combo, mask,
                              processor_ids=proc_ids, link_ids=link_ids,
                              defaultable=True)

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
            multicast_entries.append(MulticastRoutingEntry(
                key_combo + i, mask + i,
                processor_ids=proc_ids, link_ids=link_ids, defaultable=True))
        mrt = UnCompressedMulticastRoutingTable(0, 0, multicast_entries)
        self.assertEqual(mrt.x, 0)
        self.assertEqual(mrt.y, 0)

        mre = mrt.multicast_routing_entries
        for entry in mre:
            self.assertIn(entry, multicast_entries)

    def test_new_multicast_routing_table_empty(self):
        """
        tests creating a basic multicast routing table
        """
        UnCompressedMulticastRoutingTable(0, 0)

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
                key_combo + i, mask + i, processor_ids=proc_ids,
                link_ids=link_ids, defaultable=True))
        mrt = UnCompressedMulticastRoutingTable(0, 0, multicast_entries)
        # We can't add an entry with the same key but different route
        with self.assertRaises(PacmanAlreadyExistsException):
            mrt.add_multicast_routing_entry(MulticastRoutingEntry(
                key_combo, mask, processor_ids=[], link_ids=link_ids,
                defaultable=True))

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
                key_combo, mask, processor_ids=proc_ids, link_ids=link_ids,
                defaultable=True))
        # We can add entries that are exactly the same
        UnCompressedMulticastRoutingTable(0, 0, multicast_entries)

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
            key_combo, mask, processor_ids=proc_ids, link_ids=link_ids,
            defaultable=True)
        multicast_entries2 = MulticastRoutingEntry(
            key_combo - 1, mask - 1, processor_ids=proc_ids, link_ids=link_ids,
            defaultable=True)
        mrt = list()

        t1 = UnCompressedMulticastRoutingTable(0, 0, [multicast_entries1])
        t2 = UnCompressedMulticastRoutingTable(1, 0, [multicast_entries2])
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

        json_obj = to_json(tables)
        file_format_schemas.validate(json_obj, "routing_tables.json")
        new_tables = from_json(json_obj)
        self.assertEqual(new_tables.get_routing_table_for_chip(0, 0), t1)
        self.assertEqual(new_tables.get_routing_table_for_chip(1, 0), t2)
        self.assertEqual(new_tables.get_routing_table_for_chip(2, 0), None)

    def test_new_multicast_routing_tables_empty(self):
        MulticastRoutingTables()

    def test_add_routing_table_for_duplicate_chip(self):
        key_combo = 0xff35
        mask = 0xffff
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        multicast_entries1 = MulticastRoutingEntry(
            key_combo, mask, processor_ids=proc_ids, link_ids=link_ids,
            defaultable=True)

        multicast_entries2 = MulticastRoutingEntry(
            key_combo - 1, mask, processor_ids=proc_ids, link_ids=link_ids,
            defaultable=True)
        mrt = list()
        mrt.append(
            UnCompressedMulticastRoutingTable(3, 0, [multicast_entries1]))
        mrt.append(
            UnCompressedMulticastRoutingTable(3, 0, [multicast_entries2]))
        with self.assertRaises(PacmanAlreadyExistsException):
            MulticastRoutingTables(mrt)

    def test_multicast_routing_table_by_partition(self):
        mrt = MulticastRoutingTableByPartition()
        partition_id = "foo"
        source_vertex = SimpleMachineVertex(sdram=None)
        entry = MulticastRoutingTableByPartitionEntry(range(2), range(4))
        mrt.add_path_entry(entry, 0, 0, source_vertex, partition_id)
        entry = MulticastRoutingTableByPartitionEntry(range(2, 4), range(4, 8))
        mrt.add_path_entry(entry, 0, 0, source_vertex, partition_id)
        entry = MulticastRoutingTableByPartitionEntry(
            range(4, 6), range(8, 12))
        mrt.add_path_entry(entry, 0, 0, source_vertex, partition_id)
        assert list(mrt.get_routers()) == [(0, 0)]
        assert len(mrt.get_entries_for_router(0, 0)) == 1
        assert next(iter(mrt.get_entries_for_router(0, 0))) == (
            source_vertex, partition_id)
        mre = mrt.get_entries_for_router(0, 0)[source_vertex, partition_id]
        assert str(mre) == (
            "None:None:False:"
            "{0, 1, 2, 3, 4, 5}:{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}")
        assert mre == mrt.get_entry_on_coords_for_edge(
            source_vertex, partition_id, 0, 0)

    def test_multicast_routing_table_by_partition_entry(self):
        with self.assertRaises(PacmanInvalidParameterException):
            MulticastRoutingTableByPartitionEntry(range(6), range(18), 4, 3)
        with self.assertRaises(ValueError):
            MulticastRoutingTableByPartitionEntry(7, 18)
        with self.assertRaises(ValueError):
            MulticastRoutingTableByPartitionEntry(6, 19)
        e1 = MulticastRoutingTableByPartitionEntry(range(6), range(18))
        e2 = MulticastRoutingTableByPartitionEntry(
            range(2), range(4), incoming_processor=4)
        e3 = MulticastRoutingTableByPartitionEntry(
            range(3, 5), range(12, 16), incoming_link=3)
        e4 = MulticastRoutingTableByPartitionEntry(2, 16)
        e5 = MulticastRoutingTableByPartitionEntry(None, None)
        assert str(e2) == "None:4:False:{0, 1}:{0, 1, 2, 3}"
        assert str(e3) == "3:None:False:{3, 4}:{12, 13, 14, 15}"
        with self.assertRaises(PacmanInvalidParameterException):
            e2.merge_entry(e3)
        e6 = e2.merge_entry(MulticastRoutingTableByPartitionEntry(
            range(3, 5), range(12, 16)))
        assert str(e2) == "None:4:False:{0, 1}:{0, 1, 2, 3}"
        assert str(e6) == (
            "None:4:False:{0, 1, 3, 4}:{0, 1, 2, 3, 12, 13, 14, 15}")
        e6 = e3.merge_entry(MulticastRoutingTableByPartitionEntry(
            range(2), range(4)))
        assert str(e3) == "3:None:False:{3, 4}:{12, 13, 14, 15}"
        assert str(e6) == (
            "3:None:False:{0, 1, 3, 4}:{0, 1, 2, 3, 12, 13, 14, 15}")
        assert str(e4.merge_entry(e5)) == "None:None:False:{2}:{16}"
        assert str(e1) == str(e5.merge_entry(e1))
        # NB: Have true object identity; we have setters!
        assert e5 != MulticastRoutingTableByPartitionEntry(None, None)


if __name__ == '__main__':
    unittest.main()
