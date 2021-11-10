# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from spinn_utilities.config_holder import set_config
from spinn_machine import MulticastRoutingEntry
from pacman.config_setup import unittest_setup
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)
from pacman.operations.router_compressors.pair_compressor import (
    pair_compressor)
from pacman.operations.router_compressors.ordered_covering_router_compressor \
    import OrderedCoveringCompressor


class TestCompressor(unittest.TestCase):

    def setUp(self):
        self.original_tables = MulticastRoutingTables()
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
        self.original_tables.add_routing_table(original_table)
        unittest_setup()
        set_config(
            "Mapping", "router_table_compress_as_far_as_possible", True)

    def check_compression(self, compressed_tables):
        for original in self.original_tables:
            compressed = compressed_tables.get_routing_table_for_chip(
                original.x, original.y)
            assert compressed.number_of_entries < original.number_of_entries
            compare_tables(original, original)

    def test_pair_compressor(self):
        compressed_tables = pair_compressor(self.original_tables)
        self.check_compression(compressed_tables)

    def test_checked_unordered_pair_compressor(self):
        compressed_tables = pair_compressor(
            self.original_tables, ordered=False, accept_overflow=False)
        self.check_compression(compressed_tables)

    def test_unordered_pair_compressor(self):
        compressed_tables = pair_compressor(
            self.original_tables, ordered=False, accept_overflow=True)
        self.check_compression(compressed_tables)

    def test_ordered_covering_compressor(self):
        compressor = OrderedCoveringCompressor()
        compressed_tables = compressor(self.original_tables)
        self.check_compression(compressed_tables)


if __name__ == '__main__':
    unittest.main()
