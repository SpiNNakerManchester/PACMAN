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
from pacman.operations.router_algorithms.ner_route import _do_route
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from collections import defaultdict
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    convert_a_route, targets_by_chip, longest_dimension_first)
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree


def route_application_graph(machine, app_graph, placements):
    """ Route an application graph
    """
    routing_tables = MulticastRoutingTableByPartition()

    # dict of app_vertex -> dict of placement -> routing tree to all internal
    # placements from that placement
    routing_trees_in = defaultdict(dict)

    # dict of app_vertex -> set of chips on which the app vertex is placed
    target_chips = dict()

    # Find places where a vertex connects to itself
    self_connected = set()
    for partition in app_graph.outgoing_edge_partitions:

        for edge in partition.edges:
            if edge.post_vertex == partition.pre_vertex:
                # If we connect to ourselves, create an all-to-all route
                routes_in, targets = _route_internal_all_to_all(
                    routing_tables, partition.pre_vertex, machine, placements,
                    partition.identifier)
                # Store the routes for later use
                routing_trees_in[partition.pre_vertex] = routes_in
                target_chips[partition.pre_vertex] = targets
                self_connected.add(partition.pre_vertex)
                break

    # Now go through the app edges and route app vertex by app vertex
    for partition in app_graph.outgoing_edge_partitions:

        # Ensure we have target chips for the source
        pre_targets = _get_targets(
            target_chips, partition.pre_vertex, placements, machine)

        # Keep track of which chips we have visited with routes for this
        # partition to ensure no looping
        routes = dict()

        # Keep track of which chips we are going to target outgoing, along with
        # their sets of final targets, so we can route to them all at once
        pre_ends = defaultdict(dict)

        # Pick a place within the source that we can route from.  Note that
        # this might not end up being the actual source in the end.
        route_pre = next(iter(pre_targets))

        is_self_connected = partition.pre_vertex in self_connected
        for edge in _edges_by_distance(partition, placements, machine):

            # Skip self-connected edges as these have been handled above
            if edge.post_vertex == partition.pre_vertex:
                continue

            # Ensure we have edges for the target
            post_targets = _get_targets(
                target_chips, edge.post_vertex, placements, machine)

            # Pick a place in the target that we can route to.  Note that
            # this might not end up being the actual target in the end.
            route_post = next(iter(post_targets))

            route_pre, route_post = _route_pre_to_post(
                route_pre, route_post, routes, machine, pre_targets,
                post_targets)
            if route_pre in pre_targets:
                _update_targets(pre_ends[route_pre], post_targets)

            # Get or generate a way to get from the edge of the post population
            # to all of the internal machine vertices
            post_trees_in = routing_trees_in[edge.post_vertex]
            post_tree_in = post_trees_in.get(route_post)
            if post_tree_in is None:
                splitter = edge.post_vertex.splitter
                for m_vertex in splitter.get_in_coming_vertices(partition):
                    placement = placements.get_placement_of_vertex(m_vertex)
                    dest_xy = (placement.x, placement.y)
                    _route_pre_to_post(route_post, dest_xy, routes, machine)
                post_tree_in = routes[route_post]
                post_trees_in[route_post] = post_tree_in

        # Produce the routes needed to get from pre ends to the destinations
        for pre_end, targets in pre_ends.items():
            if is_self_connected:
                _convert_a_route_self_connected(
                    routing_tables, partition, None, None, routes[pre_end],
                    targets)
            else:
                convert_a_route(
                    routing_tables, partition.pre_vertex, partition.identifier,
                    None, None, routes[pre_end], targets)

        # If not self-connected, we need to link all pre-machine vertices to
        # every pre-end vertex
        if not is_self_connected:
            # TODO:
            pass

    # Return the routing tables
    return routing_tables


def _route_internal_all_to_all(
        routing_tables, app_vertex, machine, placements, partition_id):
    """ Route all machine vertices of an app vertex to themselves
    """
    routing_trees_by_placement = dict()
    targets = targets_by_chip(
        app_vertex.machine_vertices, placements, machine)
    edges = _edges_by_chip(targets, machine)
    for source_vertex in app_vertex.machine_vertices:
        source_xy = placements.get_placement_of_vertex(source_vertex).chip
        routing_tree = _do_route(
            source_xy, app_vertex.machine_vertices, machine, placements,
            longest_dimension_first)

        # Convert the routes here as they will be needed anyway
        placement = placements.get_placement_of_vertex(source_vertex)
        convert_a_route(
            routing_tables, source_vertex, partition_id, placement.p, None,
            routing_tree, targets)
        if (placement.x, placement.y) in edges:
            routing_trees_by_placement[placement] = routing_tree

    return routing_trees_by_placement, targets


def _edges_by_chip(targets, machine):
    """ Find the "edges" of the targets i.e. those targets that can be reached
        directly from outside of the targets.
    """
    edges = set()
    for x, y in targets:
        for link in range(6):
            n_x, n_y = machine.xy_over_link(x, y, link)
            if machine.is_chip_at(n_x, n_y) and (n_x, n_y) not in targets:
                edges.add((x, y))
    return edges


def _get_targets(target_chips, vertex, placements, machine):
    if vertex in target_chips:
        return target_chips[vertex]
    targets = targets_by_chip(vertex.machine_vertices, placements, machine)
    target_chips[vertex] = targets
    return targets


def _update_targets(existing, targets):
    for (x, y), (cores, links) in targets.items():
        existing_cores, existing_links = existing.get((x, y), (list(), list()))
        existing_links.extend(links)
        existing_cores.extend(cores)
        existing[x, y] = (existing_cores, existing_links)


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


def _multi_route(source_xys, target_xys, machine):
    # Dict of (x, y) to routing tree node
    routes = dict()

    for source_xy in source_xys:
        routes[source_xy] = RoutingTree(source_xy)

        for target_xy in target_xys:
            vector = machine.get_vector(source_xy, target_xy)
            nodes = longest_dimension_first(vector, source_xy, machine)
            start = source_xy

            # Avoid overlapping an existing route by cutting off the route
            # at an existing point if found
            for i, (_direction, dest_chip) in reversed(list(enumerate(nodes))):
                if dest_chip in routes:
                    nodes = nodes[i + 1:]
                    start = dest_chip
                    break

            # Convert to a routing tree by traversal
            source_node = routes[start]
            for direction, dest_chip in nodes:
                dest_node = RoutingTree(dest_chip)
                routes[dest_chip] = dest_node
                source_node.append_child((direction, dest_node))
                source_node = dest_node


def _convert_a_route_self_connected(
        routing_tables, source_partition, incoming_processor,
        incoming_link, route, targets_by_chip):
    """
    Converts the algorithm specific partition_route back to standard spinnaker
    and ands it to the routing_tables.

    :param MulticastRoutingTableByPartition routing_tables:
        spinnaker format routing tables
    :param AbstractSingleSourcePartition partition:
        Partition this route applies to
    :param int or None incoming_processor: processor this link came from
    :param int or None incoming_link: link this link came from
    :param RoutingTree route: algorithm specific format of the route
    :param dict((int,int),(list,list)): targets_by_chip:
        Target links and cores of things on the route that are final end points
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
    if (x, y) in targets_by_chip:
        cores, links = targets_by_chip[x, y]
        processor_ids.extend(cores)
        link_ids.extend(links)

    for m_vertex in source_partition.pre_vertex.machine_vertices:
        entry = MulticastRoutingTableByPartitionEntry(
            link_ids, processor_ids, incoming_processor, incoming_link)
        routing_tables.add_path_entry(
            entry, x, y, m_vertex, source_partition.identifier)

    for next_hop, next_incoming_link in next_hops:
        convert_a_route(
            routing_tables, source_partition.pre_vertex,
            source_partition.identifier, None, next_incoming_link, next_hop,
            targets_by_chip)
