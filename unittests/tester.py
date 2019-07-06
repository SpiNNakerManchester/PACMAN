import json
import time
from pacman.model.routing_tables.multicast_routing_tables import (
    to_json, from_json)
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import (
        MundyRouterCompressor)
from pacman.operations.router_compressors.unordered_compressor import \
    UnorderedCompressor
from pacman.operations.router_compressors.check_compressed import compare_tables
#original_tables = from_json("D:\spinnaker\my_spinnaker\synfire_routing_tables.json")
original_tables = from_json("D:\spinnaker\my_spinnaker\malloc_hard_routing_tables.json")

#original_tables = from_json("D:\spinnaker\my_spinnaker\malloc_routing_tables.json")
#bad_tables = from_json("D:\spinnaker\my_spinnaker\malloc_hard_routing_tables.json")
#good_tables = MulticastRoutingTables()
#for table in original_tables:
#    if table.x == 12 and table.y == 24:
#        bad_tables.add_routing_table(table)
#    else:
#        good_tables.add_routing_table(table)
#with open("D:\spinnaker\my_spinnaker\malloc_easy_routing_tables.json", "w") as f:
#    json.dump(to_json(good_tables), f)
#with open("D:\spinnaker\my_spinnaker\malloc_hard_routing_tables.json", "w") as f:
#    json.dump(to_json(bad_tables), f)

MUNDY = True
mundy_compressor = MundyRouterCompressor()
pre_compressor = UnorderedCompressor()

if MUNDY:
    start = time.time()
    mundy_tables = mundy_compressor(original_tables)
mundy_time = time.time()
pre_tables = pre_compressor(original_tables)
pre_time = time.time()
if MUNDY:
    both_tables = mundy_compressor(pre_tables)
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
    pre = pre_tables.get_routing_table_for_chip(original.x, original.y)
    pre_routes = set()
    for entry in pre.multicast_routing_entries:
        pre_routes.add(entry.spinnaker_route)
    compare_tables(original, pre)
    if MUNDY:
        both = both_tables.get_routing_table_for_chip(original.x, original.y)
        both_routes = set()
        for entry in both.multicast_routing_entries:
            both_routes.add(entry.spinnaker_route)
        compare_tables(original, both)

    if MUNDY:
        print("org:", original.number_of_entries, len(org_routes),
              "mundy:", mundy.number_of_entries, len(mundy_routes),
            "pre:", pre.number_of_entries, len(pre_routes),
            "both:", both.number_of_entries, len(both_routes))
    else:
        print("org:", original.number_of_entries, len(org_routes),
            "pre:", pre.number_of_entries, len(pre_routes))
if MUNDY:
    print(mundy_time-start)
print(pre_time-mundy_time)
if MUNDY:
    print(both_time-pre_time)
