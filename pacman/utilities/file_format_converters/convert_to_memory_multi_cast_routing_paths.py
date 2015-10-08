"""
ConvertToMemoryMultiCastRoutingPaths
"""
from pacman.model.routing_paths.multicast_routing_path_entry import \
    MulticastRoutingPathEntry
from pacman.model.routing_paths.multicast_routing_paths import \
    MulticastRoutingPaths
from pacman.utilities import file_format_schemas

import json
import os
import jsonschema


class ConvertToMemoryMultiCastRoutingPaths(object):
    """
    ConvertToMemoryMultiCastRoutingPaths: converts between file routing paths
    and the pacman representation of the routing paths
    """

    def __init__(self):
        self._multi_cast_routing_paths = MulticastRoutingPaths()
        self._direction_translation = {
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
            "LINK_0": (False, 0),
            "LINK_1": (False, 1),
            "LINK_2": (False, 2),
            "LINK_3": (False, 3),
            "LINK_4": (False, 4),
            "LINK_5": (False, 5)
        }

    def __call__(self, file_routing_paths, partitioned_graph, placements,
                 machine):

        # load the json files
        file_routing_paths = self._handle_json_files(file_routing_paths)

        # iterate though the path for each edge and create entries
        for edge_id in file_routing_paths:
            vertex = partitioned_graph.get_source_subvertex_with_label(edge_id)
            # if the vertex is none, its a vertex with the special skills of
            # needing no cores. therefore ignore
            if vertex is not None:
                placement = placements.get_placement_of_subvertex(vertex)
                self._create_entries_for_path(
                    edge_id, file_routing_paths[edge_id], None, placement.p,
                    partitioned_graph, machine, placements)

        return {'routing_paths': self._multi_cast_routing_paths}

    def _create_entries_for_path(
            self, edge_id, edge_path, source_link_id, source_p,
            partitioned_graph, machine, placements):
        """

        :param edge_id:
        :param edge_path:
        :param partitioned_graph:
        :param source_x:
        :param source_y:
        :param placements:
        :return:
        """
        chip_coords = edge_path['chip']
        memory_edges = []
        for child in edge_path['children']:
            direction_data = self._direction_translation[child['route'].upper()]
            next_hop = child['next_hop']
            if source_p is None:
                self._handle_none_core_level_entries(
                    direction_data, edge_id, next_hop, partitioned_graph,
                    machine, placements, chip_coords, source_link_id,
                    memory_edges)
            else:
                memory_edges += self._handle_core_level_entry(
                    placements, chip_coords, source_p, partitioned_graph,
                    edge_id, direction_data, next_hop, machine)
        return memory_edges

    def _handle_none_core_level_entries(
            self, direction_data, edge_id, next_hop, partitioned_graph,
            machine, placements, chip_coords, source_link_id, memory_edges):
        if direction_data[0]:
            local_memory_edges = self._create_entries_for_path(
                edge_id, next_hop, direction_data[1], None,
                partitioned_graph, machine, placements)
            memory_edges += local_memory_edges
            for memory_edge in local_memory_edges:
                entry = MulticastRoutingPathEntry(
                    router_x=chip_coords[0], router_y=chip_coords[1],
                    edge=memory_edge, out_going_links=None,
                    outgoing_processors=direction_data[1],
                    incoming_processor=None,
                    incoming_link=source_link_id)

                # add entry to system
                self._multi_cast_routing_paths.add_path_entry(entry)
        else:
            local_memory_edges = self._create_entries_for_path(
                edge_id, next_hop, direction_data[1], None,
                partitioned_graph, machine, placements)
            memory_edges += local_memory_edges
            for memory_edge in local_memory_edges:
                entry = MulticastRoutingPathEntry(
                    router_x=chip_coords[0], router_y=chip_coords[1],
                    edge=memory_edge,
                    out_going_links=direction_data[1],
                    outgoing_processors=None, incoming_processor=None,
                    incoming_link=source_link_id)
                # add entry to system
                self._multi_cast_routing_paths.add_path_entry(entry)

    def _handle_core_level_entry(
            self, placements, chip_coords, source_p, partitioned_graph,
            edge_id, direction_data, next_hop, machine):
        """

        :param placements:
        :param chip_coords:
        :param source_p:
        :param partitioned_graph:
        :param edge_id:
        :param direction_data:
        :return:
        """
        # create list holder
        memory_edges = []

        # create correct entries
        if direction_data[0]:
            # locate edge this core is associated with
            subvertex = placements.get_subvertex_on_processor(
                chip_coords[0], chip_coords[1], direction_data[1])
            memory_edge = \
                partitioned_graph.get_subedge_with_label(edge_id, subvertex)
            entry = MulticastRoutingPathEntry(
                router_x=chip_coords[0], router_y=chip_coords[1],
                edge=memory_edge, outgoing_processors=direction_data[1],
                out_going_links=None, incoming_processor=source_p,
                incoming_link=None)
            memory_edges.append(memory_edge)

            # add entry to system
            self._multi_cast_routing_paths.add_path_entry(entry)
        else:
            local_memory_edges = self._create_entries_for_path(
                edge_id, next_hop, direction_data[1], None,
                partitioned_graph, machine, placements)
            memory_edges += local_memory_edges
            for memory_edge in local_memory_edges:
                entry = MulticastRoutingPathEntry(
                    router_x=chip_coords[0], router_y=chip_coords[1],
                    edge=memory_edge, outgoing_processors=None,
                    out_going_links=direction_data[1],
                    incoming_processor=source_p,
                    incoming_link=None)

                # add entry to system
                self._multi_cast_routing_paths.add_path_entry(entry)

        # search for new hops if needed
        if isinstance(next_hop, dict):
            local_memory_edges = self._create_entries_for_path(
                edge_id, next_hop, direction_data[1], None,
                partitioned_graph, machine, placements)
            memory_edges += local_memory_edges
            return memory_edges
        else:
            return memory_edges

    @staticmethod
    def _handle_json_files(file_routing_paths):
        """

        :param file_routing_paths:
        :return:
        """
        file_routing_paths_file = open(file_routing_paths, "r")
        file_routing_paths = json.load(file_routing_paths_file)

        # validate the json files against the schemas
        # verify that the files meet the schema.
        # locate schemas
        file_routing_paths_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "routes.json"
        )
        # open readers for schemas and read in schema
        file_to_read = open(file_routing_paths_schema_file_path, "r")
        routing_paths_schema = json.load(file_to_read)

        # vlaidate json file from json schema
        jsonschema.validate(
            file_routing_paths, routing_paths_schema)

        return file_routing_paths
