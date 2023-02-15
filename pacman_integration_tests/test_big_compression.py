# Copyright (c) 2017 The University of Manchester
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

import os
import time
import sys
import unittest

from spinn_utilities.config_holder import set_config
from pacman.config_setup import unittest_setup
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)
from pacman.operations.router_compressors.ordered_covering_router_compressor \
    import OrderedCoveringCompressor
from pacman.operations.router_compressors import UnorderedPairCompressor


class TestBigCompression(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_big(self):
        set_config("Mapping", "router_table_compress_as_far_as_possible", True)
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        j_router = os.path.join(path, "malloc_hard_routing_tables.json.gz")
        original_tables = from_json(j_router)

        mundy_compressor = OrderedCoveringCompressor()
        pre_compressor = UnorderedPairCompressor()

        start = time.time()
        mundy_tables = mundy_compressor(original_tables, True)
        mundy_time = time.time()
        pre_tables = pre_compressor(original_tables, True)
        pre_time = time.time()
        both_tables = mundy_compressor(pre_tables, True)
        both_time = time.time()
        for original in original_tables:
            org_routes = set()
            for entry in original.multicast_routing_entries:
                org_routes.add(entry.spinnaker_route)
            mundy = mundy_tables.get_routing_table_for_chip(
                original.x, original.y)
            mundy_routes = set()
            for entry in mundy.multicast_routing_entries:
                mundy_routes.add(entry.spinnaker_route)
            compare_tables(original, mundy)
            pre = pre_tables.get_routing_table_for_chip(original.x, original.y)
            pre_routes = set()
            for entry in pre.multicast_routing_entries:
                pre_routes.add(entry.spinnaker_route)
            compare_tables(original, pre)
            both = both_tables.get_routing_table_for_chip(
                original.x, original.y)
            both_routes = set()
            for entry in both.multicast_routing_entries:
                both_routes.add(entry.spinnaker_route)
            compare_tables(original, both)

            print("org:", original.number_of_entries, len(org_routes),
                  "mundy:", mundy.number_of_entries, len(mundy_routes),
                  "pre:", pre.number_of_entries, len(pre_routes),
                  "both:", both.number_of_entries, len(both_routes))
        print("Mundy", mundy_time-start)
        print("Unordered", pre_time-mundy_time)
        print("Mundy after Unordered", both_time-pre_time)
