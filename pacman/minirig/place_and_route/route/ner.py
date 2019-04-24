"""Neighbour Exploring Routing (NER) algorithm from J. Navaridas et al.

Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast routing,
Parallel Computing (2014).

`http://dx.doi.org/10.1016/j.parco.2015.01.002`
"""

import heapq

from collections import deque

from pacman.minirig.geometry import concentric_hexagons, to_xyz, \
    shortest_mesh_path_length, shortest_mesh_path, \
    shortest_torus_path_length, shortest_torus_path

from pacman.minirig.place_and_route.route.utils import longest_dimension_first, links_between

from pacman.minirig.place_and_route.route.exceptions import MachineHasDisconnectedSubregion

from pacman.minirig.place_and_route.constraints import RouteEndpointConstraint

from pacman.minirig.place_and_route.machine import Cores

from pacman.minirig.links import Links
from pacman.minirig.routing_table.entries import Routes

from pacman.minirig.place_and_route.routing_tree import RoutingTree


_concentric_hexagons = {}
"""Memoized concentric_hexagons outputs, as lists.  Access via
:py:func:`.memoized_concentric_hexagons`.
"""


def memoized_concentric_hexagons(radius):
    """A memoized wrapper around :py:func:`rig.geometry.concentric_hexagons`
    which memoizes the coordinates and stores them as a tuple. Note that the
    caller must manually offset the coordinates as required.

    This wrapper is used to avoid the need to repeatedly call
    :py:func:`rig.geometry.concentric_hexagons` for every sink in a network.
    This results in a relatively minor speedup (but at equally minor cost) in
    large networks.
    """
    out = _concentric_hexagons.get(radius)
    if out is None:
        out = tuple(concentric_hexagons(radius))
        _concentric_hexagons[radius] = out
    return out


def ner_net(source, destinations, width, height, wrap_around=False, radius=10):
    """Produce a shortest path tree for a given net using NER.

    This is the kernel of the NER algorithm.

    Parameters
    ----------
    source : (x, y)
        The coordinate of the source vertex.
    destinations : iterable([(x, y), ...])
        The coordinates of destination vertices.
    width : int
        Width of the system (nodes)
    height : int
        Height of the system (nodes)
    wrap_around : bool
        True if wrap-around links should be used, false if they should be
        avoided.
    radius : int
        Radius of area to search from each node. 20 is arbitrarily selected in
        the paper and shown to be acceptable in practice.

    Returns
    -------
    (:py:class:`~.rig.place_and_route.routing_tree.RoutingTree`,
     {(x,y): :py:class:`~.rig.place_and_route.routing_tree.RoutingTree`, ...})
        A RoutingTree is produced rooted at the source and visiting all
        destinations but which does not contain any vertices etc. For
        convenience, a dictionarry mapping from destination (x, y) coordinates
        to the associated RoutingTree is provided to allow the caller to insert
        these items.
    """
    # Map from (x, y) to RoutingTree objects
    route = {source: RoutingTree(source)}

    # Handle each destination, sorted by distance from the source, closest
    # first.
    for destination in sorted(destinations,
                              key=(lambda destination:
                                   shortest_mesh_path_length(
                                       to_xyz(source), to_xyz(destination))
                                   if not wrap_around else
                                   shortest_torus_path_length(
                                       to_xyz(source), to_xyz(destination),
                                       width, height))):
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
        concentric_hexagons = memoized_concentric_hexagons(radius)
        if len(concentric_hexagons) < len(route) / 3:
            # Original approach: Start looking for route nodes in a concentric
            # spiral pattern out from the destination node.
            for x, y in concentric_hexagons:
                x += destination[0]
                y += destination[1]
                if wrap_around:
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
                if wrap_around:
                    distance = shortest_torus_path_length(
                        to_xyz(candidate_neighbour), to_xyz(destination),
                        width, height)
                else:
                    distance = shortest_mesh_path_length(
                        to_xyz(candidate_neighbour), to_xyz(destination))

                if distance <= radius and (neighbour is None or
                                           distance < neighbour_distance):
                    neighbour = candidate_neighbour
                    neighbour_distance = distance

        # Fall back on routing directly to the source if no nodes within radius
        # hops of the destination was found.
        if neighbour is None:
            neighbour = source

        # Find the shortest vector from the neighbour to this destination
        if wrap_around:
            vector = shortest_torus_path(to_xyz(neighbour),
                                         to_xyz(destination),
                                         width, height)
        else:
            vector = shortest_mesh_path(to_xyz(neighbour), to_xyz(destination))

        # The longest-dimension-first route may inadvertently pass through an
        # already connected node. If the route is allowed to pass through that
        # node it would create a cycle in the route which would be VeryBad(TM).
        # As a result, we work backward through the route and truncate it at
        # the first point where the route intersects with a connected node.
        ldf = longest_dimension_first(vector, neighbour, width, height)
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

            last_node.children.append((Routes(direction), this_node))
            last_node = this_node

    return (route[source], route)


def copy_and_disconnect_tree(root, machine):
    """Copy a RoutingTree (containing nothing but RoutingTrees), disconnecting
    nodes which are not connected in the machine.

    Note that if a dead chip is part of the input RoutingTree, no corresponding
    node will be included in the copy. The assumption behind this is that the
    only reason a tree would visit a dead chip is because a route passed
    through the chip and wasn't actually destined to arrive at that chip. This
    situation is impossible to confirm since the input routing trees have not
    yet been populated with vertices. The caller is responsible for being
    sensible.

    Parameters
    ----------
    root : :py:class:`~rig.place_and_route.routing_tree.RoutingTree`
        The root of the RoutingTree that contains nothing but RoutingTrees
        (i.e. no children which are vertices or links).
    machine : :py:class:`~rig.place_and_route.Machine`
        The machine in which the routes exist.

    Returns
    -------
    (root, lookup, broken_links)
        Where:
        * `root` is the new root of the tree
          :py:class:`~rig.place_and_route.routing_tree.RoutingTree`
        * `lookup` is a dict {(x, y):
          :py:class:`~rig.place_and_route.routing_tree.RoutingTree`, ...}
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

        if old_node.chip in machine:
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
            if direction in links_between(new_parent.chip,
                                          new_node.chip,
                                          machine):
                # Is connected via working link
                new_parent.children.append((direction, new_node))
            else:
                # Link to parent is dead (or original parent was dead and the
                # new parent is not adjacent)
                broken_links.add((new_parent.chip, new_node.chip))

        # Copy children
        for child_direction, child in old_node.children:
            to_visit.append((new_node, child_direction, child))

    return (new_root, new_lookup, broken_links)


def a_star(sink, heuristic_source, sources, machine, wrap_around):
    """Use A* to find a path from any of the sources to the sink.

    Note that the heuristic means that the search will proceed towards
    heuristic_source without any concern for any other sources. This means that
    the algorithm may miss a very close neighbour in order to pursue its goal
    of reaching heuristic_source. This is not considered a problem since 1) the
    heuristic source will typically be in the direction of the rest of the tree
    and near by and often the closest entity 2) it prevents us accidentally
    forming loops in the rest of the tree since we'll stop as soon as we touch
    any part of it.

    Parameters
    ----------
    sink : (x, y)
    heuristic_source : (x, y)
        An element from `sources` which is used as a guiding heuristic for the
        A* algorithm.
    sources : set([(x, y), ...])
    machine : :py:class:`~rig.place_and_route.Machine`
    wrap_around : bool
        Consider wrap-around links in heuristic distance calculations.

    Returns
    -------
    [(:py:class:`~rig.routing_table.Routes`, (x, y)), ...]
        A path starting with a coordinate in `sources` and terminating at
        connected neighbour of `sink` (i.e. the path does not include `sink`).
        The direction given is the link down which to proceed from the given
        (x, y) to arrive at the next point in the path.

    Raises
    ------
    :py:class:~rig.place_and_route.exceptions.MachineHasDisconnectedSubregion`
        If a path cannot be found.
    """
    # Select the heuristic function to use for distances
    if wrap_around:
        heuristic = (lambda node:
                     shortest_torus_path_length(to_xyz(node),
                                                to_xyz(heuristic_source),
                                                machine.width, machine.height))
    else:
        heuristic = (lambda node:
                     shortest_mesh_path_length(to_xyz(node),
                                               to_xyz(heuristic_source)))

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

        # Try all neighbouring locations. Note: link identifiers are from the
        # perspective of the neighbour, not the current node!
        for neighbour_link in Links:
            vector = neighbour_link.opposite.to_vector()
            neighbour = ((node[0] + vector[0]) % machine.width,
                         (node[1] + vector[1]) % machine.height)

            # Skip links which are broken
            if (neighbour[0], neighbour[1], neighbour_link) not in machine:
                continue

            # Skip neighbours who have already been visited
            if neighbour in visited:
                continue

            # Explore all other neighbours
            visited[neighbour] = (neighbour_link, node)
            heapq.heappush(to_visit, (heuristic(neighbour), neighbour))

    # Fail of no paths exist
    if selected_source is None:
        raise MachineHasDisconnectedSubregion(
            "Could not find path from {} to {}".format(
                sink, heuristic_source))

    # Reconstruct the discovered path, starting from the source we found and
    # working back until the sink.
    path = [(Routes(visited[selected_source][0]), selected_source)]
    while visited[path[-1][1]][1] != sink:
        node = visited[path[-1][1]][1]
        direction = Routes(visited[node][0])
        path.append((direction, node))

    return path


def route_has_dead_links(root, machine):
    """Quickly determine if a route uses any dead links.

    Parameters
    ----------
    root : :py:class:`~rig.place_and_route.routing_tree.RoutingTree`
        The root of the RoutingTree which contains nothing but RoutingTrees
        (i.e. no vertices and links).
    machine : :py:class:`~rig.place_and_route.Machine`
        The machine in which the routes exist.

    Returns
    -------
    bool
        True if the route uses any dead/missing links, False otherwise.
    """
    for direction, (x, y), routes in root.traverse():
        for route in routes:
            if (x, y, route) not in machine:
                return True
    return False


def avoid_dead_links(root, machine, wrap_around=False):
    """Modify a RoutingTree to route-around dead links in a Machine.

    Uses A* to reconnect disconnected branches of the tree (due to dead links
    in the machine).

    Parameters
    ----------
    root : :py:class:`~rig.place_and_route.routing_tree.RoutingTree`
        The root of the RoutingTree which contains nothing but RoutingTrees
        (i.e. no vertices and links).
    machine : :py:class:`~rig.place_and_route.Machine`
        The machine in which the routes exist.
    wrap_around : bool
        Consider wrap-around links in pathfinding heuristics.

    Returns
    -------
    (:py:class:`~.rig.place_and_route.routing_tree.RoutingTree`,
     {(x,y): :py:class:`~.rig.place_and_route.routing_tree.RoutingTree`, ...})
        A new RoutingTree is produced rooted as before. A dictionarry mapping
        from (x, y) to the associated RoutingTree is provided for convenience.

    Raises
    ------
    :py:class:~rig.place_and_route.exceptions.MachineHasDisconnectedSubregion`
        If a path to reconnect the tree cannot be found.
    """
    # Make a copy of the RoutingTree with all broken parts disconnected
    root, lookup, broken_links = copy_and_disconnect_tree(root, machine)

    # For each disconnected subtree, use A* to connect the tree to *any* other
    # disconnected subtree. Note that this process will eventually result in
    # all disconnected subtrees being connected, the result is a fully
    # connected tree.
    for parent, child in broken_links:
        child_chips = set(c.chip for c in lookup[child])

        # Try to reconnect broken links to any other part of the tree
        # (excluding this broken subtree itself since that would create a
        # cycle).
        path = a_star(child, parent,
                      set(lookup).difference(child_chips),
                      machine, wrap_around)

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
                        node.children.remove(dn[0])
                        # A node can only have one parent so we can stop now.
                        break
            last_node.children.append((Routes(last_direction), new_node))
            last_node = new_node
            last_direction = direction
        last_node.children.append((last_direction, lookup[child]))

    return (root, lookup)


def route(vertices_resources, nets, machine, constraints, placements,
          allocations={}, core_resource=Cores, radius=20):
    """Routing algorithm based on Neighbour Exploring Routing (NER).

    Algorithm refrence: J. Navaridas et al. SpiNNaker: Enhanced multicast
    routing, Parallel Computing (2014).
    http://dx.doi.org/10.1016/j.parco.2015.01.002

    This algorithm attempts to use NER to generate routing trees for all nets
    and routes around broken links using A* graph search. If the system is
    fully connected, this algorithm will always succeed though no consideration
    of congestion or routing-table usage is attempted.

    Parameters
    ----------
    radius : int
        Radius of area to search from each node. 20 is arbitrarily selected in
        the paper and shown to be acceptable in practice. If set to zero, this
        method is becomes longest dimension first routing.
    """
    wrap_around = machine.has_wrap_around_links()

    # Vertices constrained to route to a specific link. {vertex: route}
    route_to_endpoint = {}
    for constraint in constraints:
        if isinstance(constraint, RouteEndpointConstraint):
            route_to_endpoint[constraint.vertex] = constraint.route

    routes = {}
    for net in nets:
        # Generate routing tree (assuming a perfect machine)
        root, lookup = ner_net(placements[net.source],
                               set(placements[sink] for sink in net.sinks),
                               machine.width, machine.height,
                               wrap_around, radius)

        # Fix routes to avoid dead chips/links
        if route_has_dead_links(root, machine):
            root, lookup = avoid_dead_links(root, machine, wrap_around)

        # Add the sinks in the net to the RoutingTree
        for sink in net.sinks:
            tree_node = lookup[placements[sink]]
            if sink in route_to_endpoint:
                # Sinks with route-to-endpoint constraints must be routed
                # in the according directions.
                tree_node.children.append((route_to_endpoint[sink], sink))
            else:
                cores = allocations.get(sink, {}).get(core_resource, None)
                if cores is not None:
                    # Sinks with the core_resource resource specified must be
                    # routed to that set of cores.
                    for core in range(cores.start, cores.stop):
                        tree_node.children.append((Routes.core(core), sink))
                else:
                    # Sinks without that resource are simply included without
                    # an associated route
                    tree_node.children.append((None, sink))
        routes[net] = root

    return routes
