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

original_tables = from_json("routing_tables_zoned.json")
print( len(original_tables.routing_tables))
