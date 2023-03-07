# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Neighbour Exploring Routing (NER) algorithm from J. Navaridas et al.

Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast routing,
Parallel Computing (2014).

`http://dx.doi.org/10.1016/j.parco.2015.01.002`

Based on
https://github.com/project-rig/rig/blob/master/rig/place_and_route/route/ner.py
https://github.com/project-rig/rig/blob/master/rig/geometry.py
https://github.com/project-rig/rig/blob/master/rig/place_and_route/route/utils.py
"""

import functools

from collections import defaultdict

from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.data import PacmanDataView
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    route_has_dead_links, avoid_dead_links, convert_a_route,
    longest_dimension_first, nodes_to_trees, vertex_xy, get_targets_by_chip,
    least_busy_dimension_first, get_app_partitions, vertex_xy_and_route)
from pacman.model.graphs.application import ApplicationVertex
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree


def _ner_net(src, destinations, machine, vector_to_nodes):
    """ Produce a shortest path tree for a given net using NER.

    This is the kernel of the NER algorithm.

    :param tuple(int,int) source:
        The coordinate (x, y) of the source vertex.
    :param iterable(tuple(int,int)) destinations:
        The coordinates of destination vertices.
    :param ~spinn_machine.Machine machine:
        machine for which routes are being generated
    :param vector_to_nodes: ??????????
    :return:
        A RoutingTree is produced rooted at the source and visiting all
        destinations but which does not contain any vertices etc.
    :rtype: RoutingTree
    """
    # The radius to check for neighbours, and the total number of chips that
    # could appear in the radius
    radius = 20
    n_nodes_radius = 1261

    # Map from (x, y) to RoutingTree objects
    route = {src: RoutingTree(src)}

    # Handle each destination, sorted by distance from the source, closest
    # first.
    sorted_dest = sorted(
        destinations, key=(lambda dest: machine.get_vector_length(src, dest)))
    for destination in sorted_dest:
        # We shall attempt to find our nearest neighbouring placed node.
        neighbour = None

        # Try to find a nearby (within radius hops) node in the routing tree
        # that we can route to (falling back on just routing to the source).
        if len(route) / 3 > n_nodes_radius:
            # This implementation scans potential neighbours in an expanding
            # radius; this is ~3x faster per iteration than the one below.
            for candidate in machine.concentric_xys(radius, destination):
                if candidate in route:
                    neighbour = candidate
                    break
        else:
            # This implementation scans the list of all route nodes created so
            # far and finds the closest node which is < radius hops.  This is
            # ~3x slower per iteration than the one above.
            neighbour_distance = None
            for candidate_neighbour in route:
                distance = machine.get_vector_length(
                    candidate_neighbour, destination)
                if distance <= radius and (
                        neighbour is None or distance < neighbour_distance):
                    neighbour = candidate_neighbour
                    neighbour_distance = distance

        # Fall back on routing directly to the source if no nodes within radius
        # hops of the destination was found.
        if neighbour is None:
            neighbour = src

        # Find the shortest vector from the neighbour to this destination
        vector = machine.get_vector(neighbour, destination)

        # The route may inadvertently pass through an
        # already connected node. If the route is allowed to pass through that
        # node it would create a cycle in the route which would be VeryBad(TM).
        # As a result, we work backward through the route and truncate it at
        # the first point where the route intersects with a connected node.
        nodes = vector_to_nodes(vector, neighbour)
        i = len(nodes)
        for _direction, (x, y) in reversed(nodes):
            i -= 1
            if (x, y) in route:
                # We've just bumped into a node which is already part of the
                # route, this becomes our new neighbour and we truncate the LDF
                # route. (Note ldf list is truncated just after the current
                # position since it gives (direction, destination) pairs).
                neighbour = (x, y)
                nodes = nodes[i + 1:]
                break

        # Take the longest dimension first route.
        nodes_to_trees(nodes, neighbour, route)

    return route[src]


def _do_route(source_xy, post_vertexes, machine, vector_to_nodes):
    """ Routing algorithm based on Neighbour Exploring Routing (NER).

    Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast
    routing, Parallel Computing (2014).
    http://dx.doi.org/10.1016/j.parco.2015.01.002

    This algorithm attempts to use NER to generate routing trees for all nets
    and routes around broken links using A* graph search. If the system is
    fully connected, this algorithm will always succeed though no consideration
    of congestion or routing-table usage is attempted.

    :param tuple(int,int) source_xy:
    :param iterable(MachineVertex) post_vertexes:
    :param ~spinn_machine.Machine machine:
    :param vector_to_nodes:
    :return:
    :rtype: RoutingTree
    """
    destinations = set(vertex_xy(post_vertex)
                       for post_vertex in post_vertexes)
    # Generate routing tree (assuming a perfect machine)
    root = _ner_net(source_xy, destinations, machine, vector_to_nodes)

    # Fix routes to avoid dead chips/links
    if route_has_dead_links(root):
        root = avoid_dead_links(root)

    return root


def _ner_route(vector_to_nodes):
    """ Performs routing using rig algorithm

    :param vector_to_nodes:
    :return:
    :rtype: MulticastRoutingTableByPartition
    """
    routing_tables = MulticastRoutingTableByPartition()

    partitions = get_app_partitions()

    progress_bar = ProgressBar(len(partitions), "Routing")

    for partition in progress_bar.over(partitions):

        source = partition.pre_vertex
        post_vertices_by_source = defaultdict(OrderedSet)
        for edge in partition.edges:
            splitter = edge.post_vertex.splitter
            target_vertices = splitter.get_source_specific_in_coming_vertices(
                source, partition.identifier)
            for tgt, srcs in target_vertices:
                for src in srcs:
                    if isinstance(src, ApplicationVertex):
                        for s in src.splitter.get_out_going_vertices(
                                partition.identifier):
                            post_vertices_by_source[s].add(tgt)

        outgoing = OrderedSet(source.splitter.get_out_going_vertices(
            partition.identifier))
        for in_part in source.splitter.get_internal_multicast_partitions():
            if in_part.identifier == partition.identifier:
                outgoing.add(in_part.pre_vertex)
                for edge in in_part.edges:
                    post_vertices_by_source[in_part.pre_vertex].add(
                        edge.post_vertex)

        machine = PacmanDataView.get_machine()
        for m_vertex in outgoing:
            post_vertexes = post_vertices_by_source[m_vertex]
            source_xy, (m_vertex, core, link) = vertex_xy_and_route(m_vertex)
            routing_tree = _do_route(
                source_xy, post_vertexes, machine, vector_to_nodes)
            targets = get_targets_by_chip(post_vertexes)
            convert_a_route(
                routing_tables, m_vertex, partition.identifier,
                core, link, routing_tree, targets)

    progress_bar.end()

    return routing_tables


def ner_route():
    """ basic ner router

    :return: a routing table by partition
    :rtype: MulticastRoutingTableByPartition
    """
    return _ner_route(longest_dimension_first)


def ner_route_traffic_aware():
    """ traffic-aware ner router

    :return: a routing table by partition
    :rtype: MulticastRoutingTableByPartition
    """
    traffic = defaultdict(lambda: 0)
    return _ner_route(
        functools.partial(least_busy_dimension_first, traffic))
