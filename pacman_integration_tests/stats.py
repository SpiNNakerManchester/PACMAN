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
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.model.routing_tables.multicast_routing_tables import (to_json)
from pacman.model.routing_tables import (
    MulticastRoutingTables, MulticastRoutingTable)
from pacman.operations.algorithm_reports.routing_compression_checker_report \
    import compare_tables
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import (
        MundyRouterCompressor)
from pacman.operations.router_compressors.unordered_compressor import \
    UnorderedCompressor

try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict

original_tables = from_json("routing_table_15_25.json")
good = MulticastRoutingTables()

for original in original_tables:
    org_routes = defaultdict(int)
    for entry in original.multicast_routing_entries:
        org_routes[entry.spinnaker_route] += 1
    count = 0
    singles = set()
    for route in org_routes:
        count += org_routes[route]
        if org_routes[route] == 1:
            singles.add(route)
        print(route, org_routes[route])
    print(len(singles), count,  original.number_of_entries)
    gtable = MulticastRoutingTable(original.x, original.y)
    for entry in original.multicast_routing_entries:
        if entry.spinnaker_route not in singles:
            gtable.add_multicast_routing_entry(entry)
    good.add_routing_table(gtable)

json_obj = to_json(good)
# dump to json file
with open("no_singles_routing_tables.json", "w") as f:
    json.dump(json_obj, f)

