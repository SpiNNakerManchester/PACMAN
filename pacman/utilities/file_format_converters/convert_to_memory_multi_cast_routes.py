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
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartitionEntry, MulticastRoutingTableByPartition)

_route_translation = {
    "CORE_0": (True, 0),
    "CORE_1": (True, 1),
    "CORE_2": (True, 2),
    "CORE_3": (True, 3),
    "CORE_4": (True, 4),
    "CORE_5": (True, 5),
    "CORE_6": (True, 6),
    "CORE_7": (True, 7),
    "CORE_8": (True, 8),
    "CORE_9": (True, 9),
    "CORE_10": (True, 10),
    "CORE_11": (True, 11),
    "CORE_12": (True, 12),
    "CORE_13": (True, 13),
    "CORE_14": (True, 14),
    "CORE_15": (True, 15),
    "CORE_16": (True, 16),
    "CORE_17": (True, 17),
    "EAST": (False, 0),
    "NORTH_EAST": (False, 1),
    "NORTH": (False, 2),
    "WEST": (False, 3),
    "SOUTH_WEST": (False, 4),
    "SOUTH": (False, 5)
}


class ConvertToMemoryMultiCastRoutes(object):
    """ Converts between file routing paths and the PACMAN representation of\
        the routes
    """

    __slots__ = []

    def __call__(self, file_routing_paths, partition_by_id):
        # load the JSON files
        file_routing_paths = self._handle_json_files(file_routing_paths)
        progress = ProgressBar(file_routing_paths,
                               "Converting to PACMAN routes")

        # iterate though the path for each edge and create entries
        routing_tables = MulticastRoutingTableByPartition()
        for partition_id in progress.over(file_routing_paths):
            partition = partition_by_id[partition_id]

            # if the vertex is none, its a vertex with the special skills of
            # needing no cores. therefore ignore
            if partition is not None:
                partition_route = file_routing_paths[partition_id]
                self._convert_next_route(
                    routing_tables, partition, 0, None, partition_route)

        return routing_tables

    @staticmethod
    def _convert_next_route(
            routing_tables, partition, incoming_processor, incoming_link,
            partition_route):
        x, y = partition_route["chip"]

        next_hops = list()
        processor_ids = list()
        link_ids = list()
        for child in partition_route["children"]:
            route = child["route"]
            next_hop = child["next_hop"]
            if route is not None:
                is_core, route_id = _route_translation[route.upper()]
                if is_core:
                    processor_ids.append(route_id)
                else:
                    link_ids.append(route_id)
                if isinstance(next_hop, dict):
                    next_incoming_link = None
                    if not is_core:
                        next_incoming_link = (route_id + 3) % 6
                    next_hops.append((next_hop, next_incoming_link))

        routing_tables.add_path_entry(MulticastRoutingTableByPartitionEntry(
            link_ids, processor_ids, incoming_processor,
            incoming_link), x, y, partition)

        for next_hop, next_incoming_link in next_hops:
            ConvertToMemoryMultiCastRoutes._convert_next_route(
                routing_tables, partition, None, next_incoming_link, next_hop)

    @staticmethod
    def _handle_json_files(file_routing_paths):
        """
        :param file_routing_paths:
        """
        with open(file_routing_paths, "r") as f:
            return json.load(f)

        # TODO: Routing Path validation is currently not possible due to
        #       recursion
        # validate the json files against the schemas
        # verify that the files meet the schema.
        # locate schemas
        # file_routing_paths_schema_file_path = os.path.join(
        #     os.path.dirname(file_format_schemas.__file__), "routes.json"
        # )
        # open readers for schemas and read in schema
        # file_to_read = open(file_routing_paths_schema_file_path, "r")
        # routing_paths_schema = json.load(file_to_read)

        # validate json file from json schema
        # jsonschema.validate(
        #    file_routing_paths, routing_paths_schema)

        # return file_routing_paths
