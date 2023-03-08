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

from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)
from pacman.operations.router_compressors.ordered_covering_router_compressor \
    import ordered_covering_compressor


class TestOrderedCoveringCompressor(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_oc_big(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        j_router = os.path.join(path,
                                "many_to_one.json.gz")
        original_tables = from_json(j_router)
        PacmanDataWriter.mock().set_precompressed(
            original_tables)

        compressed_tables = ordered_covering_compressor()
        for original in original_tables:
            compressed = compressed_tables.get_routing_table_for_chip(
                original.x, original.y)
            compare_tables(original, compressed)
