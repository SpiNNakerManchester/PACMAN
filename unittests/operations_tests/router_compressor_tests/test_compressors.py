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
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.operations.algorithm_reports.routing_compression_checker_report \
    import compare_tables
from pacman.operations.router_compressors.pair_compressor import (
    PairCompressor)
from pacman.operations.router_compressors.unordered_compressor import (
    UnorderedCompressor)
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import (MundyRouterCompressor)


class MyTestCase(unittest.TestCase):

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

    def check_compression(self, compressed_tables):
        for original in self.original_tables:
            compressed = compressed_tables.get_routing_table_for_chip(
                original.x, original.y)
            assert compressed.number_of_entries < original.number_of_entries
            compare_tables(original, original)

    def test_pair_compressor(self):
        compressor = PairCompressor()
        compressed_tables = compressor(self.original_tables)
        self.check_compression(compressed_tables)

    def test_unordered_compressor(self):
        compressor = UnorderedCompressor()
        compressed_tables = compressor(self.original_tables)
        self.check_compression(compressed_tables)

    def test_mundy_compressor(self):
        compressor = MundyRouterCompressor()
        compressed_tables = compressor(self.original_tables)
        self.check_compression(compressed_tables)


if __name__ == '__main__':
    unittest.main()
