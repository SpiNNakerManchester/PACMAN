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
from pacman.operations.router_algorithms.ner_route import (
    _do_route, _longest_dimension_first, _convert_a_route)
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition)


def route_application_graph(machine, app_graph, placements):
    """ Route an application graph
    """
    routing_tables = MulticastRoutingTableByPartition()

    # Go through each partition, and choose a placement to be the
    # "contact point"
    contact_points = dict()
    routing_trees_in = dict()
    for partition in app_graph.outgoing_edge_partitions:

        # Work out if there are internal edges
        is_internal = False
        for edge in partition:
            if edge.post_vertex == partition.pre_vertex:
                is_internal = True
                break

        # If there are internal edges, we need to route all edges to all
        # other edges first, but then pick one of the points as the "contact
        # point"
        if is_internal:
            contact_point, routing_tree_in = _route_internal_all_to_all(
                routing_tables, partition.pre_vertex, machine, placements,
                partition.identifier)

        # Otherwise, pick a contact point and route all internal vertices to it
        # and from it
        else:
            contact_point, routing_tree_in = _route_internal_to_from_point(
                routing_tables, partition.pre_vertex, machine, placements,
                partition.identifier)

        # Store for the next loop
        contact_points[partition.pre_vertex] = contact_point
        routing_trees_in[partition.pre_vertex] = routing_tree_in

    # Now go through the app edges and route app vertex by app vertex
    for partition in app_graph.outgoing_edge_partitions:
        start = contact_points[edge.pre_vertex]
        for edge in partition.edges:
            end = contact_points[edge.post_vertex]
            _route_from_to(
                start.vertex, partition.identifier, [end], machine, placements,
                routing_tables)
            _convert_a_route(
                routing_tables, start.vertex, partition.id, None, None,
                routing_trees_in[end.vertex])

    # Return the routing tables
    return routing_tables


def _route_internal_all_to_all(
        routing_tables, app_vertex, machine, placements, partition_id):
    # Route everything all-to-all
    max_placement = None
    for source_vertex in app_vertex.machine_vertices:
        placement = _route_from_to(
            source_vertex, partition_id, app_vertex.machine_vertices,
            machine, placements, routing_tables)
        if max_placement is None:
            max_placement = placement
        elif max_placement.x < placement.x or max_placement.y < placement.y:
            max_placement = placement

    # Keep the routing from the connection point to the vertices for later use
    routing_tree_in = _do_route(
        max_placement.vertex, app_vertex.machine_vertices, machine, placements,
        _longest_dimension_first)

    return max_placement, routing_tree_in


def _route_internal_to_from_point(
        routing_tables, app_vertex, machine, placements, partition_id):

    # Find a place to route to/from
    max_placement = None
    for source_vertex in app_vertex.machine_vertices:
        placement = placements.get_placement_of_vertex(source_vertex)
        if max_placement is None:
            max_placement = placement
        elif max_placement.x < placement.x or max_placement.y < placement.y:
            max_placement = placement

    for source_vertex in app_vertex.machine_vertices:
        # Do the routing from the sources to the connection point
        _route_from_to(
            source_vertex, partition_id, [max_placement.vertex], machine,
            placements, routing_tables)

    # Keep the routing from the connection point to the vertices for later use
    routing_tree_in = _do_route(
        max_placement.vertex, app_vertex.machine_vertices, machine, placements,
        _longest_dimension_first)

    return max_placement, routing_tree_in


def _route_from_to(
        source_vertex, partition_id, target_vertices, machine, placements,
        routing_tables):
    routing_tree = _do_route(
        source_vertex, target_vertices, machine, placements,
        _longest_dimension_first)
    placement = placements.get_placement_of_vertex(source_vertex)
    _convert_a_route(
        routing_tables, source_vertex, partition_id, placement.p, None,
        routing_tree)
    return placement
