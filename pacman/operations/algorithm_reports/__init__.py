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
from .network_specification import NetworkSpecification
from .router_collision_potential_report import RouterCollisionPotentialReport
from .router_summary import RouterSummary
from .write_json_machine import WriteJsonMachine
from .write_json_machine_graph import WriteJsonMachineGraph
from .write_json_partition_n_keys_map import WriteJsonPartitionNKeysMap
from .write_json_placements import WriteJsonPlacements
from .write_json_routing_tables import WriteJsonRoutingTables

reports_metadata_file = os.path.join(
    os.path.dirname(__file__), "reports_metadata.xml")

__all__ = (
    "NetworkSpecification",
    "RouterCollisionPotentialReport",
    "RouterSummary",
    "WriteJsonMachine",
    "WriteJsonMachineGraph",
    "WriteJsonPartitionNKeysMap",
    "WriteJsonPlacements",
    "WriteJsonRoutingTables"
    )
