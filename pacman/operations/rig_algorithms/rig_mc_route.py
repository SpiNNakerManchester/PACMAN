from pacman.operations.rig_algorithms.ner import do_route

from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from pacman.operations.rig_algorithms.routing_tree import RoutingTree
from pacman.operations.rig_algorithms.routes import Routes


def convert_a_route(
        routing_tables, partition, incoming_processor, incoming_link,
        partition_route):
    x, y = partition_route.chip

    next_hops = list()
    processor_ids = list()
    link_ids = list()
    for (route, next_hop) in partition_route.children:
        if route is not None:
            link = None
            if isinstance(route, Routes):
                if route.is_core:
                    processor_ids.append(route.core_num)
                else:
                    link = route.value
                    link_ids.append(link)
            elif isinstance(route, int):
                link_ids.append(route)
            if isinstance(next_hop, RoutingTree):
                next_incoming_link = None
                if link is not None:
                    next_incoming_link = (link + 3) % 6
                next_hops.append((next_hop, next_incoming_link))

    entry = MulticastRoutingTableByPartitionEntry(
        link_ids, processor_ids, incoming_processor, incoming_link)
    routing_tables.add_path_entry(entry, x, y, partition)

    for next_hop, next_incoming_link in next_hops:
        convert_a_route(
            routing_tables, partition, None, next_incoming_link, next_hop)


class RigMCRoute(object):
    """ Performs routing using rig algorithm
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, placements):
        """

        :param machine_graph:
        :param machine:
        :param placements:  pacman.model.placements.placements.py
        :return:
        """
        routing_tables = MulticastRoutingTableByPartition()

        progress_bar = ProgressBar(len(machine_graph.vertices), "Routing")

        for source_vertex in progress_bar.over(machine_graph.vertices):
            # handle the vertex edges
            for partition in machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(
                        source_vertex):
                if partition.traffic_type == EdgeTrafficType.MULTICAST:
                    post_vertexes = list(
                        e.post_vertex for e in partition.edges)
                    routingtree = do_route(
                        source_vertex, post_vertexes, machine, placements)
                    convert_a_route(routing_tables, partition, 0, None,
                                    routingtree)

        progress_bar.end()

        return routing_tables
