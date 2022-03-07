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

import os
import sys
import unittest
from spinn_utilities.config_holder import set_config
from pacman.config_setup import unittest_setup
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.model.routing_tables.uncompressed_multicast_routing_table import (
    from_csv)
from pacman.operations.router_compressors import (
    RangeCompressor, range_compressor)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)


class TestRangeCompressor(unittest.TestCase):

    def setUp(self):
        unittest_setup()
        set_config(
            "Mapping", "router_table_compress_as_far_as_possible", True)

    def test_big(self):
        path = os.path.dirname(sys.modules[self.__module__].__file__)
        table_path = os.path.join(path, "table1.csv.gz")
        table = from_csv(table_path)
        compressor = RangeCompressor()
        compressed = compressor.compress_table(table)
        compare_tables(table, compressed)

    def test_tables(self):
        tables = MulticastRoutingTables()
        path = os.path.dirname(sys.modules[self.__module__].__file__)
        table_path = os.path.join(path, "table2.csv.gz")
        table = from_csv(table_path)
        tables.add_routing_table(table)
        compressed = range_compressor(tables)
        c_table = compressed.get_routing_table_for_chip(0, 0)
        compare_tables(table, c_table)


if __name__ == '__main__':
    unittest.main()
