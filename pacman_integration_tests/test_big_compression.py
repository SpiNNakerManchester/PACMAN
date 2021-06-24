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
