import os
import time
import sys
import unittest

from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.operations.algorithm_reports.routing_compression_checker_report \
    import compare_tables
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import (
        MundyRouterCompressor)
from pacman.operations.router_compressors.unordered_compressor import \
    UnorderedCompressor


class TestBigCompression(unittest.TestCase):

    def test_big(self):
        class_file = sys.modules[self.__module__].__file__
        path = os.path.dirname(os.path.abspath(class_file))
        j_router = os.path.join(path, "malloc_hard_routing_tables.json.gz")
        original_tables = from_json(j_router)

        mundy_compressor = MundyRouterCompressor()
        # Hack to stop it throwing a wobly for too many entries
        MundyRouterCompressor.max_supported_length = 5000
        pre_compressor = UnorderedCompressor()

        start = time.time()
        mundy_tables = mundy_compressor(original_tables)
        mundy_time = time.time()
        pre_tables = pre_compressor(original_tables)
        pre_time = time.time()
        both_tables = mundy_compressor(pre_tables)
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
