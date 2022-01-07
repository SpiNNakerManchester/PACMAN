# Copyright (c) 2021 The University of Manchester
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
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from collections import defaultdict
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first)
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree


class _Targets(object):
    """ A set of targets to be added to a route on a chip
    """
    __slots__ = ["__cores_by_source"]

    def __init__(self):
        self.__cores_by_source = defaultdict(list)

    def add_sources_for_core(self, core, source_vertices):
        """ Add a set of vertices that target a given core
        """
        for vertex in source_vertices:
            self.__cores_by_source[vertex].append(core)

    @property
    def cores_by_source(self):
        """ Get a list of (source, list of cores) for the targets
        """
        return self.__cores_by_source.items()


def route_application_graph(machine, app_graph, placements):
    """ Route an application graph
    """
    routing_tables = MulticastRoutingTableByPartition()

    # Keep track of all chips in each application vertex.  This allows routes
    # between vertices to be filtered so that they only include chips outside
    # of those containing the application vertex.
    incoming_chips = dict()
    outgoing_chips = dict()

    # Now go through the app edges and route app vertex by app vertex
    for partition in app_graph.outgoing_edge_partitions:
        # Store the source vertex of the partition
        source = partition.pre_vertex

        # Pick a place within the source that we can route from.  Note that
        # this might not end up being the actual source in the end.
        source_chip, source_chips = _get_outgoing_chips(
            outgoing_chips, partition.pre_vertex, partition.identifier,
            placements)

        # Keep track of the source edge chips
        source_edge_chips = set()

        # Keep track of which chips we have visited with routes for this
        # partition to ensure no looping
        routes = dict()

        # Keep track of cores or links to target on specific chips
        targets = defaultdict(_Targets)

        # Remember if we see a self-connection
        self_connected = False

        for edge in _edges_by_distance(partition, placements, machine):
            # Store the target vertex
            target = edge.post_vertex

            # Pick a place in the target that we can route to.  Note that
            # this might not end up being the actual target in the end.
            target_chip, target_chips = _get_incoming_chips(
                incoming_chips, edge.post_vertex, partition.identifier,
                placements)

            # If not self-connected
            if source != target:

                # Make a route between source and target
                source_edge_chip, target_edge_chip = _route_pre_to_post(
                    source_chip, target_chip, routes, machine,
                    source_chips, target_chips)

                # Route from target edge chip to all the targets
                for chip in target_chips:
                    _route_pre_to_post(target_edge_chip, chip, routes, machine)

                if source_edge_chip in source_chips:
                    source_edge_chips.add(source_edge_chip)

            # If self-connected
            else:
                self_connected = True

            # Add the target cores that need to be hit
            target_vertices = \
                target.splitter.get_source_specific_in_coming_vertices(
                    source, partition.identifier)
            for tgt, srcs in target_vertices:
                # TODO: Deal with virtual vertices
                place = placements.get_placement_of_vertex(tgt)
                targets[place.chip].add_sources_for_core(place.p, srcs)

        for source_edge_chip in source_edge_chips:
            _convert_a_route(
                routing_tables, source, partition.identifier, None, None,
                routes[source_edge_chip], targets=targets)

        if self_connected:
            # If self-connected, the sources are also the targets
            for chip in target_chips:
                source_edge_chips.add(chip)

        source_routes = dict()
        for chip in source_chips:
            for edge_chip in source_edge_chips:
                _route_pre_to_post(chip, edge_chip, source_routes, machine)
            _convert_a_route(
                routing_tables, source, partition.identifier, None, None,
                source_routes[chip], targets=targets)

    # Return the routing tables
    return routing_tables


def _get_incoming_chips(incoming_chips, app_vertex, partition_id, placements):
    # TODO: Deal with virtual chips
    if app_vertex in incoming_chips:
        return incoming_chips[app_vertex]
    vertex_chips = defaultdict(list)
    for m_vertex in app_vertex.splitter.get_in_coming_vertices(partition_id):
        place = placements.get_placement_of_vertex(m_vertex)
        vertex_chips[place.chip].append(place)
    first_chip = next(iter(vertex_chips.keys()))
    data = (first_chip, vertex_chips)
    incoming_chips[app_vertex] = data
    return data


def _get_outgoing_chips(outgoing_chips, app_vertex, partition_id, placements):
    # TODO: Deal with virtual chips
    if app_vertex in outgoing_chips:
        return outgoing_chips[app_vertex]
    vertex_chips = defaultdict(list)
    for m_vertex in app_vertex.splitter.get_out_going_vertices(partition_id):
        place = placements.get_placement_of_vertex(m_vertex)
        vertex_chips[place.chip].append(place)
    first_chip = next(iter(vertex_chips.keys()))
    data = (first_chip, vertex_chips)
    outgoing_chips[app_vertex] = data
    return data


def _route_pre_to_post(
        source_xy, dest_xy, routes, machine, source_group=None,
        target_group=None):
    # Find a route from source to target
    vector = machine.get_vector(source_xy, dest_xy)
    nodes = longest_dimension_first(vector, source_xy, machine)

    # Start from the end and move backwards until we find a chip
    # not in the source group, or a already in the route
    route_pre = source_xy
    for i, (_direction, (x, y)) in reversed(list(enumerate(nodes))):
        if _in_group((x, y), source_group) or (x, y) in routes:
            nodes = nodes[i + 1:]
            route_pre = (x, y)
            break

    # If we found one not in the route, create a new entry for it
    if route_pre not in routes:
        routes[route_pre] = RoutingTree(route_pre)

    # Start from the start and move forwards until we find a chip in
    # the target group
    route_post = dest_xy
    if target_group is not None:
        for i, (_direction, (x, y)) in enumerate(nodes):
            if (x, y) in target_group:
                nodes = nodes[:i + 1]
                route_post = (x, y)
                break

    # Convert nodes to routes and add to existing routes
    source_route = routes[route_pre]
    for direction, dest_node in nodes:
        dest_route = RoutingTree(dest_node)
        routes[dest_node] = dest_route
        source_route.append_child((direction, dest_route))
        source_route = dest_route

    return route_pre, route_post


def _in_group(item, group):
    if group is None:
        return False
    return item in group


def _edges_by_distance(partition, placements, machine):
    pre_xy = placements.get_placement_of_vertex(
        next(iter(partition.pre_vertex.machine_vertices))).chip
    return sorted(
        partition.edges,
        key=lambda edge: machine.get_vector_length(
            pre_xy, placements.get_placement_of_vertex(
                next(iter(edge.post_vertex.machine_vertices))).chip))


def _convert_a_route(
        routing_tables, source_vertex, partition_id, incoming_processor,
        incoming_link, route, route_source_by_machine=None, targets=None):
    """ Convert the algorithm specific partition_route back to SpiNNaker and
        adds it to the routing_tables.

    :param MulticastRoutingTableByPartition routing_tables:
        spinnaker format routing tables
    :param source_vertex: The source to be added to the table
    :type source_vertex: ApplicationVertex or MachineVertex
    :param incoming_processor: processor this link came from
    :type incoming_processor: int or None
    :param incoming_link: link this link came from
    :type incoming_link: int or None
    :param RoutingTree route: algorithm specific format of the route
    :param route_source_by_machine:
        Whether to use the app vertex or machine vertices in the routing table
        for the first entry.  Do not use if source_vertex is a MachineVertex,
        as otherwise errors will occur!
    :type bool or None
    :param targets:
        Targets for each chip.  When present for a chip, the route links and
        cores are added to each entry in the targets.
    :type targets: dict(tuple(int,int),_Targets) or None
    """
    x, y = route.chip

    next_hops = list()
    processor_ids = list()
    link_ids = list()
    for (route, next_hop) in route.children:
        if route is not None:
            link_ids.append(route)
            next_incoming_link = (route + 3) % 6
        if next_hop is not None:
            next_hops.append((next_hop, next_incoming_link))

    if targets is not None and (x, y) in targets:
        chip_targets = targets[x, y]
        for (source, additional_cores) in chip_targets.cores_by_source:
            entry = MulticastRoutingTableByPartitionEntry(
                link_ids, processor_ids + additional_cores, incoming_processor,
                incoming_link)
            routing_tables.add_path_entry(entry, x, y, source, partition_id)

    else:
        entry = MulticastRoutingTableByPartitionEntry(
            link_ids, processor_ids, incoming_processor, incoming_link)
        if route_source_by_machine is None or not route_source_by_machine:
            routing_tables.add_path_entry(
                entry, x, y, source_vertex, partition_id)
        else:
            for m_vertex in source_vertex.splitter.get_out_going_vertices(
                    partition_id):
                routing_tables.add_path_entry(
                    entry, x, y, m_vertex, partition_id)

    for next_hop, next_incoming_link in next_hops:
        # On the next hop, we can set route_source_by_machine to False
        _convert_a_route(
            routing_tables, source_vertex, partition_id, None,
            next_incoming_link, next_hop, False, targets)
