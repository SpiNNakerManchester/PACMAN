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
from .routing_tree import RoutingTree
from pacman.data import PacmanDataView
from pacman.exceptions import MachineHasDisconnectedSubRegion
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartitionEntry)
from pacman.model.graphs import (
    AbstractFPGA, AbstractSpiNNakerLink, AbstractVirtual)
from pacman.model.graphs.application import ApplicationEdgePartition
from collections import deque, defaultdict
import heapq
import itertools


def get_app_partitions():
    """ Find all application partitions.

        Note that where a vertex splitter indicates that it has internal
        partitions but is not the source of an external partition, a "fake"
        empty application partition is added.  This allows the calling
        algorithm to loop over the returned list and look at the set of
        edges *and* internal partitions to get a complete picture of *all*
        targets for each source machine vertex at once.

    Note that where a vertex splitter indicates that it has internal
        partitions but is not the source of an external partition, a "fake"
        empty application partition is added.  This allows the calling
        algorithm to loop over the returned list and look at the set of
        edges and internal partitions to get a complete picture of all
        targets for each source machine vertex at once.

    :return: list of partitions; note where there are only internal multicast
        partitions, the partition will have no edges.  Caller should use
        vertex.splitter.get_internal_multicast_partitions for details.
    :rtype: list(ApplicationEdgePartition)
    """

    # Find all partitions that need to be dealt with
    # Make a copy which we can edit
    partitions = list(PacmanDataView.iterate_partitions())
    sources = set(p.pre_vertex for p in partitions)

    # Convert internal partitions to self-connected partitions
    for v in PacmanDataView.iterate_vertices():
        internal_partitions = v.splitter.get_internal_multicast_partitions()
        if v not in sources and internal_partitions:
            part_ids = set(p.identifier for p in internal_partitions)
            for identifier in part_ids:
                # Add a partition with no edges to identify this as internal
                app_part = ApplicationEdgePartition(identifier, v)
                partitions.append(app_part)
    return partitions


def route_has_dead_links(root):
    """ Quickly determine if a route uses any dead links.

    :param RoutingTree root:
        The root of the RoutingTree which contains nothing but RoutingTrees
        (i.e. no vertices and links).
    :return: True if the route uses any dead/missing links, False otherwise.
    :rtype: bool
    """
    for _, (x, y), routes in root.traverse():
        chip = PacmanDataView.get_chip_at(x, y)
        for route in routes:
            if chip is None:
                return True
            if not chip.router.is_link(route):
                return True
    return False


def avoid_dead_links(root):
    """ Modify a RoutingTree to route-around dead links in a Machine.

    Uses A* to reconnect disconnected branches of the tree (due to dead links
    in the machine).

    :param RoutingTree root:
        The root of the RoutingTree which contains nothing but RoutingTrees
        (i.e. no vertices and links).
    :return:
        A new RoutingTree is produced rooted as before.
    :rtype: RoutingTree
    """
    # Make a copy of the RoutingTree with all broken parts disconnected
    root, lookup, broken_links = _copy_and_disconnect_tree(root)

    # For each disconnected subtree, use A* to connect the tree to *any* other
    # disconnected subtree. Note that this process will eventually result in
    # all disconnected subtrees being connected, the result is a fully
    # connected tree.
    for parent, child in broken_links:
        child_chips = set(c.chip for c in lookup[child])

        # Try to reconnect broken links to any other part of the tree
        # (excluding this broken subtree itself since that would create a
        # cycle).
        path = a_star(child, parent, set(lookup).difference(child_chips))

        # Add new RoutingTree nodes to reconnect the child to the tree.
        last_node = lookup[path[0][1]]
        last_direction = path[0][0]
        for direction, (x, y) in path[1:]:
            if (x, y) not in child_chips:
                # This path segment traverses new ground so we must create a
                # new RoutingTree for the segment.
                new_node = RoutingTree((x, y))
                # A* will not traverse anything but chips in this tree so this
                # assert is meerly a sanity check that this occurred correctly.
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

    return root


def _copy_and_disconnect_tree(root):
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

    :param RoutingTree root:
        The root of the RoutingTree that contains nothing but RoutingTrees
        (i.e. no children which are vertices or links).
    :return: (root, lookup, broken_links)
        Where:
        * `root` is the new root of the tree
          :py:class:`~.RoutingTree`
        * `lookup` is a dict {(x, y):
          :py:class:`~.RoutingTree`, ...}
        * `broken_links` is a set ([(parent, child), ...]) containing all
          disconnected parent and child (x, y) pairs due to broken links.
    :rtype: tuple(RoutingTree, dict(tuple(int,int),RoutingTree),
        set(tuple(tuple(int,int),tuple(int,int))))
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
        machine = PacmanDataView.get_machine()
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
        else:
            if new_node is not new_parent:
                # If this node is not dead, check connectivity to parent
                # node (no reason to check connectivity between a dead node
                # and its parent).
                if _is_linked(
                        new_parent.chip, new_node.chip, direction, machine):
                    # Is connected via working link
                    new_parent.append_child((direction, new_node))
                else:
                    # Link to parent is dead (or original parent was dead and
                    # the new parent is not adjacent)
                    broken_links.add((new_parent.chip, new_node.chip))

        # Copy children
        for child_direction, child in old_node.children:
            to_visit.append((new_node, child_direction, child))

    return new_root, new_lookup, broken_links


def a_star(sink, heuristic_source, sources):
    """ Use A* to find a path from any of the sources to the sink.

    Note that the heuristic means that the search will proceed towards
    heuristic_source without any concern for any other sources. This means that
    the algorithm may miss a very close neighbour in order to pursue its goal
    of reaching heuristic_source. This is not considered a problem since 1) the
    heuristic source will typically be in the direction of the rest of the tree
    and near by and often the closest entity 2) it prevents us accidentally
    forming loops in the rest of the tree since we'll stop as soon as we touch
    any part of it.

    :param tuple(int,int) sink: (x, y)
    :param tuple(int,int) heuristic_source: (x, y)
        An element from `sources` which is used as a guiding heuristic for the
        A* algorithm.
    :param set(tuple(int,int)) sources: set([(x, y), ...])
    :return: [(int, (x, y)), ...]
        A path starting with a coordinate in `sources` and terminating at
        connected neighbour of `sink` (i.e. the path does not include `sink`).
        The direction given is the link down which to proceed from the given
        (x, y) to arrive at the next point in the path.
    :rtype: list(tuple(int,tuple(int,int)))
    """
    machine = PacmanDataView.get_machine()
    # Select the heuristic function to use for distances
    heuristic = (lambda the_node: machine.get_vector_length(
        the_node, heuristic_source))

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


def _is_linked(source, target, direction, machine):
    """
    :param tuple(int,int) source:
    :param tuple(int,int) target:
    :param int direction:
    :param ~spinn_machine.Machine machine:
    :rtype: bool
    """
    s_chip = machine.get_chip_at(source[0], source[1])
    if s_chip is None:
        return False
    link = s_chip.router.get_link(direction)
    if link is None:
        return False
    if link.destination_x != target[0]:
        return False
    if link.destination_y != target[1]:
        return False
    return True


def convert_a_route(
        routing_tables, source_vertex, partition_id, incoming_processor,
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
        Target cores and links of things on the route that are final end points
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

    entry = MulticastRoutingTableByPartitionEntry(
        link_ids, processor_ids, incoming_processor, incoming_link)
    routing_tables.add_path_entry(entry, x, y, source_vertex, partition_id)

    for next_hop, next_incoming_link in next_hops:
        convert_a_route(
            routing_tables, source_vertex, partition_id, None,
            next_incoming_link, next_hop, targets_by_chip)


def longest_dimension_first(vector, start):
    """
    List the (x, y) steps on a longest-dimension first route.

    :param tuple(int,int,int) vector: (x, y, z)
        The vector which the path should cover.
    :param tuple(int,int) start: (x, y)
        The coordinates from which the path should start (note this is a 2D
        coordinate).
    :param ~spinn_machine.Machine machine:
    :return:
    :rtype: list(tuple(int,tuple(int, int)))
    """
    return vector_to_nodes(
        sorted(enumerate(vector), key=(lambda x: abs(x[1])), reverse=True),
        start)


def least_busy_dimension_first(traffic, vector, start):
    """ List the (x, y) steps on a route that goes through the least busy\
        routes first.

    :param traffic: A dictionary of (x, y): count of routes
    :param vector: (x, y, z)
        The vector which the path should cover.
    :param start: (x, y)
        The coordinates from which the path should start (note this is a 2D
        coordinate).
    :param machine:the spinn machine.
    :return: min route
    """

    # Go through and find the sum of traffic depending on the route taken
    min_sum = 0
    min_route = None
    for order in itertools.permutations([0, 1, 2]):
        dm_vector = [(i, vector[i]) for i in order]
        route = vector_to_nodes(dm_vector, start)
        sum_traffic = sum(traffic[x, y] for _, (x, y) in route)
        if min_route is None or min_sum > sum_traffic:
            min_sum = sum_traffic
            min_route = route

    for _, (x, y) in min_route:
        traffic[x, y] += 1

    return min_route


def vector_to_nodes(dm_vector, start):
    """ Convert a vector to a set of nodes

    :param list(tuple(int,int)) dm_vector:
        A vector made up of a list of (dimension, magnitude), where dimensions
        are x=0, y=1, z=diagonal=2
    :param tuple(int,int) start: The x, y coordinates of the start
    :return: A list of (link_id, (target_x, target_y)) of nodes on a route
    :rtype: list(tuple(int,tuple(int, int)))
    """
    machine = PacmanDataView.get_machine()
    x, y = start

    out = []

    for dimension, magnitude in dm_vector:
        if magnitude == 0:
            continue

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


def nodes_to_trees(nodes, start, route):
    """ Convert a list of nodes into routing trees, adding them to existing
        routes

    :param list(tuple(int,tuple(int,int))) nodes:
        The list of (link_id, (target_x, target_y)) nodes on the route
    :param tuple(int,int) start: The start of the route
    :param dict(tuple(int,int),RoutingTree) route:
        Existing routing trees, with key (x, y) coordinates of the chip of the
        routes.
    """
    last_node = route.get(start)
    if last_node is None:
        last_node = RoutingTree(start)
        route[start] = last_node
    for direction, (x, y) in nodes:
        this_node = RoutingTree((x, y))
        route[(x, y)] = this_node

        last_node.append_child((direction, this_node))
        last_node = this_node


def most_direct_route(source, dest, machine):
    """ Find the most direct route from source to target on the machine

    :param tuple(int,int) source: The source x, y coordinates
    :param tuple(int,int) dest: The destination x, y coordinated
    :param Machine machine: The machine on which to route
    """
    vector = machine.get_vector(source, dest)
    nodes = longest_dimension_first(vector, source)
    route = dict()
    nodes_to_trees(nodes, source, route)
    root = route[source]
    if route_has_dead_links(root):
        root = avoid_dead_links(root)
    return root


def get_targets_by_chip(vertices):
    """ Get the target links and cores on the relevant chips

    :param list(MachineVertex) vertices: The vertices to target
    :param Placements placements: Where the vertices are placed
    :return: A dict of (x, y) to target (cores, links)
    :rtype: dict((int, int), (list, list))
    """
    by_chip = defaultdict(lambda: (set(), set()))
    for vertex in vertices:
        x, y = vertex_xy(vertex)
        if isinstance(vertex, AbstractVirtual):
            # Sinks with route-to-endpoint constraints must be routed
            # in the according directions.
            link = route_to_endpoint(vertex)
            by_chip[x, y][1].add(link)
        else:
            core = PacmanDataView.get_placement_of_vertex(vertex).p
            by_chip[x, y][0].add(core)
    return by_chip


def _get_link_data(vertex):
    """ Get link data from an abstract virtual vertex

    :param AbstractVirtual vertex: The vertex to find the link data for
    :rtype: AbstractLinkData
    """
    machine = PacmanDataView.get_machine()
    if isinstance(vertex, AbstractFPGA):
        return machine.get_fpga_link_with_id(
            vertex.fpga_id, vertex.fpga_link_id, vertex.board_address,
            vertex.linked_chip_coordinates)
    if isinstance(vertex, AbstractSpiNNakerLink):
        return machine.get_spinnaker_link_with_id(
            vertex.spinnaker_link_id, vertex.board_address,
            vertex.linked_chip_coordinates)
    raise TypeError(f"Vertex {vertex} has unknown type")


def vertex_xy(vertex):
    """
    :param MachineVertex vertex:
    :param Placements placements:
    :param ~spinn_machine.Machine machine:
    :rtype: tuple(int,int)
    """
    if not isinstance(vertex, AbstractVirtual):
        placement = PacmanDataView.get_placement_of_vertex(vertex)
        return placement.x, placement.y
    link_data = _get_link_data(vertex)
    return link_data.connected_chip_x, link_data.connected_chip_y


def vertex_xy_and_route(vertex):
    """ Get the non-virtual chip coordinates, the vertex, and processor or
        link to follow to get to the vertex

    :param MachineVertex vertex:
    :return: the xy corridinates of the target vertex mapped to a tuple of
        the vertex, core and link.
        One of core or link is provided the other is None
    :rtype: tuple(tuple(int, int), tuple(MachineVertex, int,  None)) or
        tuple(tuple(int, int), tuple(MachineVertex, None, int))
    """
    if not isinstance(vertex, AbstractVirtual):
        placement = PacmanDataView.get_placement_of_vertex(vertex)
        return (placement.x, placement.y), (vertex, placement.p, None)
    link_data = _get_link_data(vertex)
    return ((link_data.connected_chip_x, link_data.connected_chip_y),
            (vertex, None, link_data.connected_link))


def route_to_endpoint(vertex):
    """
    :param MachineVertex vertex:
    :param ~spinn_machine.Machine machine:
    :rtype: int
    """
    link_data = _get_link_data(vertex)
    return link_data.connected_link
