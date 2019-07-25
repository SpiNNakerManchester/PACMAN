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

import json
import time
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.model.routing_tables.multicast_routing_tables import (to_json)
from pacman.model.routing_tables import (MulticastRoutingTables)
from pacman.operations.algorithm_reports.routing_compression_checker_report \
    import compare_tables
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import (
        MundyRouterCompressor)
from pacman.operations.router_compressors import (
    AbstractCompressor, ClashCompressor, PairCompressor, UnorderedCompressor)


#original_tables = from_json("malloc_hard_routing_tables.json.gz")
original_tables = from_json("routing_tables_speader_big.json.gz")

bad = MulticastRoutingTables()
#good = MulticastRoutingTables()
#for original in original_tables:
#    if original.x ==19 and original.y == 22:
#        bad.add_routing_table(original)
    #else:
    #    bad.add_routing_table(original)

#json_obj = to_json(bad)
# dump to json file
#with open("routing_tables_zoned_bad1.json", "w") as f:
#    json.dump(json_obj, f)
#json_obj = to_json(good)
# dump to json file
#with open("routing_tables_zoned_2000.json", "w") as f:
#    json.dump(json_obj, f)
#original_tables = bad

MUNDY = False
PRE = False
PAIR = True
CLASH = True
# Hack to stop it throwing a wobly for too many entries
AbstractCompressor.MAX_SUPPORTED_LENGTH = 500000
clash_compressor = ClashCompressor()
mundy_compressor = MundyRouterCompressor()
pre_compressor = UnorderedCompressor()
pair_compressor = PairCompressor()

if MUNDY:
    start = time.time()
    mundy_tables = mundy_compressor(original_tables)
mundy_time = time.time()
if PRE:
    pre_tables = pre_compressor(original_tables)
pre_time = time.time()
if MUNDY and PRE:
    both_tables = mundy_compressor(pre_tables)
both_time = time.time()
if PAIR:
    pair_tables = pair_compressor(original_tables)
pair_time = time.time()
if CLASH:
    clash_tables = clash_compressor(original_tables)
clash_time = time.time()
for original in original_tables:
    org_routes = set()
    for entry in original.multicast_routing_entries:
        org_routes.add(entry.spinnaker_route)
    if MUNDY:
        mundy = mundy_tables.get_routing_table_for_chip(original.x, original.y)
        mundy_routes = set()
        for entry in mundy.multicast_routing_entries:
            if entry.spinnaker_route == 32:
                print(entry)
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
    if CLASH:
        clash = clash_tables.get_routing_table_for_chip(original.x, original.y)
        clash_routes = set()
        for entry in clash.multicast_routing_entries:
            clash_routes.add(entry.spinnaker_route)
        compare_tables(original, clash)

    result = "x: {} y: {} Org:{} ".format(original.x, original.y, original.number_of_entries)
    if PRE:
        result += "pre:{} ".format(pre.number_of_entries)
    if MUNDY:
        result += "mundy:{} ".format(mundy.number_of_entries)
        if PRE:
            result += "both:{} ".format(both.number_of_entries)
    if PAIR:
        result += "pair:{} ".format(pair.number_of_entries)
    if CLASH:
        result += "clash:{} ".format(clash.number_of_entries)
    print(result)
if MUNDY:
    print("Mundy time", mundy_time-start)
if PRE:
    print("Pre time", pre_time-mundy_time)
if MUNDY and PRE:
    print("Both time", both_time-pre_time)
if PAIR:
    print("Pair time", pair_time - both_time)
if CLASH:
    print("Clash time", clash_time - pair_time)

"""
routing_tables_zoned_bad.json
x: 18 y: 26 Org:2770 pair:1040 clash:1020 
x: 19 y: 22 Org:2435 pair:1024 clash:996 
x: 22 y: 26 Org:2881 pair:1214 clash:1185 
x: 19 y: 25 Org:2001 pair:1069 clash:1025 
"""