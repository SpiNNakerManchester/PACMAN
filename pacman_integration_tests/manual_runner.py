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

import json
import time
from spinn_utilities.config_holder import set_config
from spinn_machine import Machine
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.model.routing_tables.multicast_routing_tables import (to_json)
from pacman.model.routing_tables import (MulticastRoutingTables)
from pacman.operations.router_compressors.routing_compression_checker import (
    compare_tables)
from pacman.operations.router_compressors.ordered_covering_router_compressor \
    import ordered_covering_compressor
from pacman.operations.router_compressors import pair_compressor
from pacman.config_setup import unittest_setup

unittest_setup()

# original_tables = from_json("routing_table_15_25.json")
original_tables = from_json("malloc_hard_routing_tables.json.gz")
# original_tables = from_json("routing_tables_speader_big.json.gz")
SPLIT = False
if SPLIT:
    bad = MulticastRoutingTables()
    good = MulticastRoutingTables()
    for original in original_tables:
        if original.x == 19 and original.y == 22:
            good.add_routing_table(original)
    else:
        bad.add_routing_table(original)

    json_obj = to_json(bad)
    # dump to json file
    with open("routing_tables_zoned_bad1.json", "w") as f:
        json.dump(json_obj, f)
    json_obj = to_json(good)
    # dump to json file
    with open("routing_tables_zoned_2000.json", "w") as f:
        json.dump(json_obj, f)
    original_tables = bad

MUNDY = True
PRE = True
PAIR = True
# Hack to stop it throwing a wobly for too many entries
Machine.ROUTER_ENTRIES = 50000
set_config("Mapping", "router_table_compress_as_far_as_possible", True)
PacmanDataWriter.mock().set_uncompressed(original_tables)

if MUNDY:
    start = time.time()
    mundy_tables = ordered_covering_compressor()
mundy_time = time.time()
if PRE:
    pre_tables = pair_compressor(ordered=False)
pre_time = time.time()
if PAIR:
    pair_tables = pair_compressor()
pair_time = time.time()
if MUNDY and PRE:
    PacmanDataWriter.mock().set_uncompressed(pre_tables)
    both_tables = ordered_covering_compressor()
both_time = time.time()
for original in original_tables:
    org_routes = set()
    for entry in original.multicast_routing_entries:
        org_routes.add(entry.spinnaker_route)
    if MUNDY:
        mundy = mundy_tables.get_routing_table_for_chip(original.x, original.y)
        mundy_routes = set()
        for entry in mundy.multicast_routing_entries:
            mundy_routes.add(entry.spinnaker_route)
        compare_tables(original, mundy)
    if PRE:
        pre = pre_tables.get_routing_table_for_chip(original.x, original.y)
        pre_routes = set()
        for entry in pre.multicast_routing_entries:
            pre_routes.add(entry.spinnaker_route)
        compare_tables(original, pre)
    if MUNDY and PRE:
        both = both_tables.get_routing_table_for_chip(original.x, original.y)
        both_routes = set()
        for entry in both.multicast_routing_entries:
            both_routes.add(entry.spinnaker_route)
        compare_tables(original, both)
    if PAIR:
        pair = pair_tables.get_routing_table_for_chip(original.x, original.y)
        pair_routes = set()
        for entry in pair.multicast_routing_entries:
            pair_routes.add(entry.spinnaker_route)
        compare_tables(original, pair)

    result = "x: {} y: {} Org:{} ".format(
        original.x, original.y, original.number_of_entries)
    if PRE:
        result += "pre:{} ".format(pre.number_of_entries)
    if MUNDY:
        result += "mundy:{} ".format(mundy.number_of_entries)
        if PRE:
            result += "both:{} ".format(both.number_of_entries)
    if PAIR:
        result += "pair:{} ".format(pair.number_of_entries)
    print(result)
if MUNDY:
    print("Mundy time", mundy_time-start)
if PRE:
    print("Pre time", pre_time-mundy_time)
if MUNDY and PRE:
    print("Both time", both_time-pre_time)
if PAIR:
    print("Pair time", pair_time - both_time)
