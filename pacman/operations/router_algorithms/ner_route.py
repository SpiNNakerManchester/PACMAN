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

"""Neighbour Exploring Routing (NER) algorithm from J. Navaridas et al.

Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast routing,
Parallel Computing (2014).

`http://dx.doi.org/10.1016/j.parco.2015.01.002`

Based on
https://github.com/project-rig/rig/blob/master/rig/place_and_route/route/ner.py
https://github.com/project-rig/rig/blob/master/rig/geometry.py
https://github.com/project-rig/rig/blob/master/rig/place_and_route/route/utils.py
"""

import heapq

from collections import deque

from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import MachineHasDisconnectedSubRegion
from pacman.model.graphs import (
    AbstractFPGAVertex, AbstractVirtualVertex, AbstractSpiNNakerLinkVertex)
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from .routing_tree import RoutingTree

_concentric_hexagons = {}
"""Memoized concentric_hexagons outputs, as lists.  Access via
:py:func:`.memoized_concentric_hexagons`.
"""


def _convert_a_route(
        routing_tables, partition, incoming_processor, incoming_link,
        partition_route):
    """
    Converts the algorithm specific partition_route back to standard spinnaker
    and ands it to the routing_tables.
    :param routing_tables:  spinnaker format routing tables
    :param partition: Partition this route applices to
    :param incoming_processor: collections of processors this link came from
    :param incoming_link: collection of links this link came from
    :param partition_route: algorithm specific format of the route
    """
    x, y = partition_route.chip

    next_hops = list()
    processor_ids = list()
    link_ids = list()
    for (route, next_hop) in partition_route.children:
        if route is not None:
            link = None
            if route >= 6:
                # The route was offset as first 6 are the links
                processor_ids.append(route - 6)
            else:
                link_ids.append(route)
            if isinstance(next_hop, RoutingTree):
                next_incoming_link = None
                if link is not None:
                    #  Same as Router.opposite just inlined for speed
                    next_incoming_link = (link + 3) % 6
                next_hops.append((next_hop, next_incoming_link))

    entry = MulticastRoutingTableByPartitionEntry(
        link_ids, processor_ids, incoming_processor, incoming_link)
    routing_tables.add_path_entry(entry, x, y, partition)

    for next_hop, next_incoming_link in next_hops:
        _convert_a_route(
            routing_tables, partition, None, next_incoming_link, next_hop)


def _memoized_concentric_hexagons(radius):
    """A memoized wrapper around concentric_hexagons`
    which memoizes the coordinates and stores them as a tuple. Note that the
    caller must manually offset the coordinates as required.

    This wrapper is used to avoid the need to repeatedly call
    concentric_hexagons` for every sink in a network.
    This results in a relatively minor speedup (but at equally minor cost) in
    large networks.
    """
    out = _concentric_hexagons.get(radius)
    if out is None:
        out = tuple(_get_concentric_hexagons(radius))
        _concentric_hexagons[radius] = out
    return out


def _ner_net(source, destinations, machine):
    """ Produce a shortest path tree for a given net using NER.

    This is the kernel of the NER algorithm.


    :param source:  (x, y)
        The coordinate of the source vertex.
    :param destinations:  iterable([(x, y), ...])
        The coordinates of destination vertices.
    :param machine: machine for which routes are being generated
    :return: (:py:class:`RoutingTree`
     {(x,y): :py:class:`RoutingTree`, ...})
        A RoutingTree is produced rooted at the source and visiting all
        destinations but which does not contain any vertices etc. For
        convenience, a dictionarry mapping from destination (x, y) coordinates
        to the associated RoutingTree is provided to allow the caller to insert
        these items.

    """
    width = machine.max_chip_x + 1
    height = machine.max_chip_y + 1
    radius = 20
    # Map from (x, y) to RoutingTree objects
    route = {source: RoutingTree(source)}

    # Handle each destination, sorted by distance from the source, closest
    # first.
    sorted_dest = sorted(
        destinations, key=(lambda destination: machine.get_vector_length(
                source, destination)))
    for destination in sorted_dest:
        # We shall attempt to find our nearest neighbouring placed node.
        neighbour = None

        # Try to find a nearby (within radius hops) node in the routing tree
        # that we can route to (falling back on just routing to the source).
        #
        # In an implementation according to the algorithm's original
        # specification looks for nodes at each point in a growing set of rings
        # of concentric hexagons. If it doesn't find any destinations this
        # means an awful lot of checks: 1261 for the default radius of 20.
        #
        # An alternative (but behaviourally identical) implementation scans the
        # list of all route nodes created so far and finds the closest node
        # which is < radius hops (falling back on the origin if no node is
        # closer than radius hops).  This implementation requires one check per
        # existing route node. In most routes this is probably a lot less than
        # 1261 since most routes will probably have at most a few hundred route
        # nodes by the time the last destination is being routed.
        #
        # Which implementation is best is a difficult question to answer:
        # * In principle nets with quite localised connections (e.g.
        #   nearest-neighbour or centroids traffic) may route slightly more
        #   quickly with the original algorithm since it may very quickly find
        #   a neighbour.
        # * In nets which connect very spaced-out destinations the second
        #   implementation may be quicker since in such a scenario it is
        #   unlikely that a neighbour will be found.
        # * In extremely high-fan-out nets (e.g. broadcasts), the original
        #   method is very likely to perform *far* better than the alternative
        #   method since most iterations will complete immediately while the
        #   alternative method must scan *all* the route vertices.
        # As such, it should be clear that neither method alone is 'best' and
        # both have degenerate performance in certain completely reasonable
        # styles of net. As a result, a simple heuristic is used to decide
        # which technique to use.
        #
        # The following micro-benchmarks are crude estimate of the
        # runtime-per-iteration of each approach (at least in the case of a
        # torus topology)::
        #
        #     $ # Original approach
        #     $ python -m timeit --setup 'x, y, w, h, r = 1, 2, 5, 10, \
        #                                     {x:None for x in range(10)}' \
        #                        'x += 1; y += 1; x %= w; y %= h; (x, y) in r'
        #     1000000 loops, best of 3: 0.207 usec per loop
        #     $ # Alternative approach
        #     $ python -m timeit --setup 'from rig.geometry import \
        #                                 shortest_torus_path_length' \
        #                        'shortest_torus_path_length( \
        #                             (0, 1, 2), (3, 2, 1), 10, 10)'
        #     1000000 loops, best of 3: 0.666 usec per loop
        #
        # From this we can approximately suggest that the alternative approach
        # is 3x more expensive per iteration. A very crude heuristic is to use
        # the original approach when the number of route nodes is more than
        # 1/3rd of the number of routes checked by the original method.
        concentric_hexagons = _memoized_concentric_hexagons(radius)
        if len(concentric_hexagons) < len(route) / 3:
            # Original approach: Start looking for route nodes in a concentric
            # spiral pattern out from the destination node.
            for x, y in concentric_hexagons:
                x += destination[0]
                y += destination[1]
                if machine.has_wrap_arounds:
                    x %= width
                    y %= height
                if (x, y) in route:
                    neighbour = (x, y)
                    break
        else:
            # Alternative approach: Scan over every route node and check to see
            # if any are < radius, picking the closest one if so.
            neighbour = None
            neighbour_distance = None
            for candidate_neighbour in route:
                distance = machine.get_vector_length(
                        candidate_neighbour, destination)
                if distance <= radius and (neighbour is None or
                                           distance < neighbour_distance):
                    neighbour = candidate_neighbour
                    neighbour_distance = distance

        # Fall back on routing directly to the source if no nodes within radius
        # hops of the destination was found.
        if neighbour is None:
            neighbour = source

        # Find the shortest vector from the neighbour to this destination
        vector = machine.get_vector(neighbour, destination)

        # The longest-dimension-first route may inadvertently pass through an
        # already connected node. If the route is allowed to pass through that
        # node it would create a cycle in the route which would be VeryBad(TM).
        # As a result, we work backward through the route and truncate it at
        # the first point where the route intersects with a connected node.
        ldf = _longest_dimension_first(vector, neighbour, machine)
        i = len(ldf)
        for direction, (x, y) in reversed(ldf):
            i -= 1
            if (x, y) in route:
                # We've just bumped into a node which is already part of the
                # route, this becomes our new neighbour and we truncate the LDF
                # route. (Note ldf list is truncated just after the current
                # position since it gives (direction, destination) pairs).
                neighbour = (x, y)
                ldf = ldf[i + 1:]
                break

        # Take the longest dimension first route.
        last_node = route[neighbour]
        for direction, (x, y) in ldf:
            this_node = RoutingTree((x, y))
            route[(x, y)] = this_node

            last_node.append_child((direction, this_node))
            last_node = this_node

    return (route[source], route)


def _is_linked(source, target, direction, machine):
    s_chip = machine.get_chip_at(source[0], source[1])
    if s_chip is None:
        return False
    link = s_chip.router.get_link(direction)
    if link is None:
        return False
    if (link.destination_x != target[0]):
        return False
    if (link.destination_y != target[1]):
        return False
    return True


def _copy_and_disconnect_tree(root, machine):
    """
    Copy a RoutingTree (containing nothing but RoutingTrees), disconnecting
    nodes which are not connected in the machine.

    Note that if a dead chip is part of the input RoutingTree, no corresponding
    node will be included in the copy. The assumption behind this is that the
    only reason a tree would visit a dead chip is because a route passed
    through the chip and wasn't actually destined to arrive at that chip. This
    situation is impossible to confirm since the input routing trees have not
    yet been populated with vertices. The caller is responsible for being
    sensible.
    :param root: :py:class:`RoutingTree`
        The root of the RoutingTree that contains nothing but RoutingTrees
        (i.e. no children which are vertices or links).
    :param machine: The machine in which the routes exist
    :return: (root, lookup, broken_links)
        Where:
        * `root` is the new root of the tree
          :py:class:`~.RoutingTree`
        * `lookup` is a dict {(x, y):
          :py:class:`~.RoutingTree`, ...}
        * `broken_links` is a set ([(parent, child), ...]) containing all
          disconnected parent and child (x, y) pairs due to broken links.
    """
    new_root = None

    # Lookup for copied routing tree {(x, y): RoutingTree, ...}
    new_lookup = {}

    # List of missing connections in the copied routing tree [(new_parent,
    # new_child), ...]
    broken_links = set()

    # A queue [(new_parent, direction, old_node), ...]
    to_visit = deque([(None, None, root)])
    while to_visit:
        new_parent, direction, old_node = to_visit.popleft()

        if machine.is_chip_at(old_node.chip[0], old_node.chip[1]):
            # Create a copy of the node
            new_node = RoutingTree(old_node.chip)
            new_lookup[new_node.chip] = new_node
        else:
            # This chip is dead, move all its children into the parent node
            assert new_parent is not None, \
                "Net cannot be sourced from a dead chip."
            new_node = new_parent

        if new_parent is None:
            # This is the root node
            new_root = new_node
        elif new_node is not new_parent:
            # If this node is not dead, check connectivity to parent node (no
            # reason to check connectivity between a dead node and its parent).
            if _is_linked(new_parent.chip, new_node.chip, direction, machine):
                # Is connected via working link
                new_parent.append_child((direction, new_node))
            else:
                # Link to parent is dead (or original parent was dead and the
                # new parent is not adjacent)
                broken_links.add((new_parent.chip, new_node.chip))

        # Copy children
        for child_direction, child in old_node.children:
            to_visit.append((new_node, child_direction, child))

    return (new_root, new_lookup, broken_links)


def _a_star(sink, heuristic_source, sources, machine):
    """
    Use A* to find a path from any of the sources to the sink.

    Note that the heuristic means that the search will proceed towards
    heuristic_source without any concern for any other sources. This means that
    the algorithm may miss a very close neighbour in order to pursue its goal
    of reaching heuristic_source. This is not considered a problem since 1) the
    heuristic source will typically be in the direction of the rest of the tree
    and near by and often the closest entity 2) it prevents us accidentally
    forming loops in the rest of the tree since we'll stop as soon as we touch
    any part of it.

    :param sink: (x, y)
    :param heuristic_source: (x, y)
        An element from `sources` which is used as a guiding heuristic for the
        A* algorithm.
    :param sources: set([(x, y), ...])
    :param machine:
    :return: [(int, (x, y)), ...]
        A path starting with a coordinate in `sources` and terminating at
        connected neighbour of `sink` (i.e. the path does not include `sink`).
        The direction given is the link down which to proceed from the given
        (x, y) to arrive at the next point in the path.

    """
    # Select the heuristic function to use for distances
    heuristic = (lambda node: machine.get_vector_length(
        node, heuristic_source))

    # A dictionary {node: (direction, previous_node}. An entry indicates that
    # 1) the node has been visited and 2) which node we hopped from (and the
    # direction used) to reach previous_node.  This may be None if the node is
    # the sink.
    visited = {sink: None}

    # The node which the tree will be reconnected to
    selected_source = None

    # A heap (accessed via heapq) of (distance, (x, y)) where distance is the
    # distance between (x, y) and heuristic_source and (x, y) is a node to
    # explore.
    to_visit = [(heuristic(sink), sink)]
    while to_visit:
        _, node = heapq.heappop(to_visit)

        # Terminate if we've found the destination
        if node in sources:
            selected_source = node
            break

        # Try all neighbouring locations.
        for neighbour_link in range(6):  # Router.MAX_LINKS_PER_ROUTER
            # Note: link identifiers arefrom the perspective of the neighbour,
            # not the current node!
            neighbour = machine.xy_over_link(
                #                  Same as Router.opposite
                node[0], node[1], (neighbour_link + 3) % 6)

            # Skip links which are broken
            if not machine.is_link_at(
                    neighbour[0], neighbour[1], neighbour_link):
                continue

            # Skip neighbours who have already been visited
            if neighbour in visited:
                continue

            # Explore all other neighbours
            visited[neighbour] = (neighbour_link, node)
            heapq.heappush(to_visit, (heuristic(neighbour), neighbour))

    # Fail of no paths exist
    if selected_source is None:
        raise MachineHasDisconnectedSubRegion(
            "Could not find path from {} to {}".format(
                sink, heuristic_source))

    # Reconstruct the discovered path, starting from the source we found and
    # working back until the sink.
    path = [(visited[selected_source][0], selected_source)]
    while visited[path[-1][1]][1] != sink:
        node = visited[path[-1][1]][1]
        direction = visited[node][0]
        path.append((direction, node))

    return path


def _route_has_dead_links(root, machine):
    """ Quickly determine if a route uses any dead links.

    :param root: :py:class:`.routing_tree.RoutingTree`
        The root of the RoutingTree which contains nothing but RoutingTrees
        (i.e. no vertices and links).
    :param machine: The machine in which the routes exist.
    :return: True if the route uses any dead/missing links, False otherwise.
    """
    for _, (x, y), routes in root.traverse():
        chip = machine.get_chip_at(x, y)
        for route in routes:
            if chip is None:
                return True
            if not chip.router.is_link(route):
                return True
    return False


def _avoid_dead_links(root, machine):
    """ Modify a RoutingTree to route-around dead links in a Machine.

    Uses A* to reconnect disconnected branches of the tree (due to dead links
    in the machine).

    :param root: :py:class:`~.routing_tree.RoutingTree`
        The root of the RoutingTree which contains nothing but RoutingTrees
        (i.e. no vertices and links).
    :param machine: The machine in which the routes exist.
    :return: (:py:class:`~.RoutingTree`,
     {(x,y): :py:class:`~.routing_tree.RoutingTree`, ...})
        A new RoutingTree is produced rooted as before. A dictionarry mapping
        from (x, y) to the associated RoutingTree is provided for convenienc
    """
    # Make a copy of the RoutingTree with all broken parts disconnected
    root, lookup, broken_links = _copy_and_disconnect_tree(root, machine)

    # For each disconnected subtree, use A* to connect the tree to *any* other
    # disconnected subtree. Note that this process will eventually result in
    # all disconnected subtrees being connected, the result is a fully
    # connected tree.
    for parent, child in broken_links:
        child_chips = set(c.chip for c in lookup[child])

        # Try to reconnect broken links to any other part of the tree
        # (excluding this broken subtree itself since that would create a
        # cycle).
        path = _a_star(child, parent,
                       set(lookup).difference(child_chips),
                       machine)
        # Add new RoutingTree nodes to reconnect the child to the tree.
        last_node = lookup[path[0][1]]
        last_direction = path[0][0]
        for direction, (x, y) in path[1:]:
            if (x, y) not in child_chips:
                # This path segment traverses new ground so we must create a
                # new RoutingTree for the segment.
                new_node = RoutingTree((x, y))
                # A* will not traverse anything but chips in this tree so this
                # assert is meerly a sanity check that this ocurred correctly.
                assert (x, y) not in lookup, "Cycle created."
                lookup[(x, y)] = new_node
            else:
                # This path segment overlaps part of the disconnected tree
                # (A* doesn't know where the disconnected tree is and thus
                # doesn't avoid it). To prevent cycles being introduced, this
                # overlapped node is severed from its parent and merged as part
                # of the A* path.
                new_node = lookup[(x, y)]

                # Find the node's current parent and disconnect it.
                for node in lookup[child]:  # pragma: no branch
                    dn = [(d, n) for d, n in node.children if n == new_node]
                    assert len(dn) <= 1
                    if dn:
                        node.remove_child(dn[0])
                        # A node can only have one parent so we can stop now.
                        break
            last_node.append_child((last_direction, new_node))
            last_node = new_node
            last_direction = direction
        last_node.append_child((last_direction, lookup[child]))

    return (root, lookup)


def _do_route(source_vertex, post_vertexes, machine, placements):
    """
    Routing algorithm based on Neighbour Exploring Routing (NER).

    Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast
    routing, Parallel Computing (2014).
    http://dx.doi.org/10.1016/j.parco.2015.01.002

    This algorithm attempts to use NER to generate routing trees for all nets
    and routes around broken links using A* graph search. If the system is
    fully connected, this algorithm will always succeed though no consideration
    of congestion or routing-table usage is attempted.

    :param source_vertex:
    :param post_vertexes:
    :param machine:
    :param placements:
    :return:
    """
    source_xy = _vertex_xy(source_vertex, placements, machine)
    destinations = set(_vertex_xy(post_vertex, placements, machine)
                       for post_vertex in post_vertexes)
    # Generate routing tree (assuming a perfect machine)
    root, lookup = _ner_net(source_xy, destinations, machine)

    # Fix routes to avoid dead chips/links
    if _route_has_dead_links(root, machine):
        root, lookup = _avoid_dead_links(root, machine)

    # Add the sinks in the net to the RoutingTree
    for post_vertex in post_vertexes:
        tree_node = lookup[_vertex_xy(post_vertex, placements, machine)]
        if isinstance(post_vertex, AbstractVirtualVertex):
            # Sinks with route-to-endpoint constraints must be routed
            # in the according directions.
            route = _route_to_endpoint(post_vertex, machine)
            tree_node.append_child((route, post_vertex))
        else:
            core = placements.get_placement_of_vertex(post_vertex).p
            if core is not None:
                #  Offset the core by 6 as first 6 are the links
                tree_node.append_child((core + 6, post_vertex))
            else:
                # Sinks without that resource are simply included without
                # an associated route
                tree_node.append_child((None, post_vertex))

    return root


def _vertex_xy(vertex, placements, machine):
    if not isinstance(vertex, AbstractVirtualVertex):
        placement = placements.get_placement_of_vertex(vertex)
        return (placement.x, placement.y)
    link_data = None
    if isinstance(vertex, AbstractFPGAVertex):
        link_data = machine.get_fpga_link_with_id(
            vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
    elif isinstance(vertex, AbstractSpiNNakerLinkVertex):
        link_data = machine.get_spinnaker_link_with_id(
            vertex.spinnaker_link_id, vertex.board_address)
    return (link_data.connected_chip_x, link_data.connected_chip_y)


def _route_to_endpoint(vertex, machine):
    if isinstance(vertex, AbstractFPGAVertex):
        link_data = machine.get_fpga_link_with_id(
            vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
    else:
        link_data = machine.get_spinnaker_link_with_id(
            vertex.spinnaker_link_id, vertex.board_address)
    return link_data.connected_link


def _get_concentric_hexagons(radius, start=(0, 0)):
    """
    A generator which produces coordinates of concentric rings of hexagons.

    :param radius:  Number of layers to produce (0 is just one hexagon)
    :param start:  (x, y)
        The coordinate of the central hexagon.
    :return:
    """
    x, y = start
    yield (x, y)
    for r in range(1, radius + 1):
        # Move to the next layer
        y -= 1
        # Walk around the hexagon of this radius
        for dx, dy in [(1, 1), (0, 1), (-1, 0), (-1, -1), (0, -1), (1, 0)]:
            for _ in range(r):
                yield (x, y)
                x += dx
                y += dy


def _longest_dimension_first(vector, start, machine):
    """
    List the (x, y) steps on a longest-dimension first route.

    :param vector: (x, y, z)
        The vector which the path should cover.
    :param start: (x, y)
        The coordinates from which the path should start (note this is a 2D
        coordinate).
    :param machine:
    :return:
    """
    x, y = start

    out = []

    for dimension, magnitude in sorted(
            enumerate(vector), key=(lambda x: abs(x[1])), reverse=True):
        if magnitude == 0:
            break

        if dimension == 0:  # x
            if magnitude > 0:
                # Move East (0) magnitude times
                for _ in range(magnitude):
                    x, y = machine.xy_over_link(x, y, 0)
                    out.append((0, (x, y)))
            else:
                # Move West (3) -magnitude times
                for _ in range(magnitude, 0):
                    x, y = machine.xy_over_link(x, y, 3)
                    out.append((3, (x, y)))
        elif dimension == 1:  # y
            if magnitude > 0:
                # Move North (2) magnitude times
                for _ in range(magnitude):
                    x, y = machine.xy_over_link(x, y, 2)
                    out.append((2, (x, y)))
            else:
                # Move South (5) -magnitude times
                for _ in range(magnitude, 0):
                    x, y = machine.xy_over_link(x, y, 5)
                    out.append((5, (x, y)))
        else:  # z
            if magnitude > 0:
                # Move SouthWest (4) magnitude times
                for _ in range(magnitude):
                    x, y = machine.xy_over_link(x, y, 4)
                    out.append((4, (x, y)))
            else:
                # Move NorthEast (1) -magnitude times
                for _ in range(magnitude, 0):
                    x, y = machine.xy_over_link(x, y, 1)
                    out.append((1, (x, y)))
    return out


class NerRoute(object):
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
                    routingtree = _do_route(
                        source_vertex, post_vertexes, machine, placements)
                    _convert_a_route(routing_tables, partition, 0, None,
                                     routingtree)

        progress_bar.end()

        return routing_tables
