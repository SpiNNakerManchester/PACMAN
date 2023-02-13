# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from spinn_utilities.config_holder import set_config
from spinn_machine import MulticastRoutingEntry
from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)
from pacman.operations.router_compressors import (
    pair_compressor, range_compressor)
from pacman.operations.router_compressors.ordered_covering_router_compressor \
    import ordered_covering_compressor


class TestCompressor(unittest.TestCase):

    def setUp(self):
        original_tables = MulticastRoutingTables()
        original_table = UnCompressedMulticastRoutingTable(x=0, y=0)
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0000, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0001, 0b1111, [0], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0101, 0b1111, [4], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1000, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1001, 0b1111, [0], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1110, 0b1111, [4], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b1100, 0b1111, [1, 2], [], False))
        original_table.add_multicast_routing_entry(
            MulticastRoutingEntry(0b0010, 0b1011, [4, 5], [], False))
        original_tables.add_routing_table(original_table)
        unittest_setup()
        set_config(
            "Mapping", "router_table_compress_as_far_as_possible", True)
        writer = PacmanDataWriter.mock()
        writer.set_uncompressed(original_tables)
        writer.set_precompressed(original_tables)

    def check_compression(self, compressed_tables):
        for original in PacmanDataView.get_precompressed():
            compressed = compressed_tables.get_routing_table_for_chip(
                original.x, original.y)
            assert compressed.number_of_entries < original.number_of_entries
            compare_tables(original, original)

    def test_pair_compressor(self):
        compressed_tables = pair_compressor()
        self.check_compression(compressed_tables)

    def test_range_compressor_skipped(self):
        compressed_tables = range_compressor()
        for original in PacmanDataView.get_uncompressed():
            compressed = compressed_tables.get_routing_table_for_chip(
                original.x, original.y)
            self.assertEqual(original, compressed)

    def test_checked_unordered_pair_compressor(self):
        compressed_tables = pair_compressor(
            ordered=False, accept_overflow=False)
        self.check_compression(compressed_tables)

    def test_unordered_pair_compressor(self):
        compressed_tables = pair_compressor(
            ordered=False, accept_overflow=True)
        self.check_compression(compressed_tables)

    def test_ordered_covering_compressor(self):
        compressed_tables = ordered_covering_compressor()
        self.check_compression(compressed_tables)


if __name__ == '__main__':
    unittest.main()
