# Copyright (c) 2017 The University of Manchester
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

import os
import sys
import unittest
from spinn_utilities.config_holder import set_config
from spinn_machine.version import FIVE
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.model.routing_tables.uncompressed_multicast_routing_table import (
    from_csv)
from pacman.operations.router_compressors import (
    RangeCompressor, range_compressor)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)


class TestRangeCompressor(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()
        # tests against version 5 as Spin2 would not need compression
        set_config("Machine", "version", str(FIVE))
        set_config(
            "Mapping", "router_table_compress_as_far_as_possible", str(True))

    def test_big(self) -> None:
        file_path = sys.modules[self.__module__].__file__
        assert file_path is not None
        path = os.path.dirname(file_path)
        assert path is not None
        table_path = os.path.join(path, "table1.csv.gz")
        table = from_csv(table_path)
        compressor = RangeCompressor()
        compressed = compressor.compress_table(table)
        compare_tables(table, compressed)

    def test_tables(self) -> None:
        tables = MulticastRoutingTables()
        file_path = sys.modules[self.__module__].__file__
        assert file_path is not None
        path = os.path.dirname(file_path)
        assert path is not None
        table_path = os.path.join(path, "table2.csv.gz")
        table = from_csv(table_path)
        tables.add_routing_table(table)
        PacmanDataWriter.mock().set_uncompressed(tables)
        compressed = range_compressor()
        c_table = compressed.get_routing_table_for_chip(0, 0)
        assert c_table is not None
        compare_tables(table, c_table)


if __name__ == '__main__':
    unittest.main()
