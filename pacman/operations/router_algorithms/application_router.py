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

from pacman.data import PacmanDataView
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first, get_app_partitions, vertex_xy,
    vertex_xy_and_route)
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree
from pacman.model.graphs.application import ApplicationVertex
from collections import deque, defaultdict
from spinn_utilities.progress_bar import ProgressBar


class _Targets(object):
    """ A set of targets to be added to a route on a chip(xy)
    """
    __slots__ = ["__targets_by_source"]

    def __init__(self):
        self.__targets_by_source = defaultdict(lambda: (list(), list()))

    def ensure_source(self, source_vertex):
        """ Ensure that a source exists, even if it targets nothing

        :param source_vertex: The vertex to ensure exists
        :type source_vertex: ApplicationVertex or MachineVertex
        """
        if source_vertex not in self.__targets_by_source:
            self.__targets_by_source[source_vertex] = (list(), list())

    def add_sources_for_target(
            self, core, link, source_vertices, partition_id):
        """ Add a set of vertices that target a given core or link

        :param core: The core to target with the sources or None if no core
        :type core: int or None
        :param link: The link to target with the sources or None if no link
        :type link: int or None
        :param source_vertices: A list of sources which target something here
        :type source_vertices: list(ApplicationVertex or MachineVertex)
        :param str partition_id: The partition of the sources
        """
        for vertex in source_vertices:
            if isinstance(vertex, ApplicationVertex):
                if self.__is_m_vertex(vertex, partition_id):
                    self.__add_m_vertices(vertex, partition_id, core, link)
                else:
                    self.__add_source(vertex, core, link)
            else:
                if vertex.app_vertex in self.__targets_by_source:
                    self.__replace_app_vertex(vertex.app_vertex, partition_id)
                self.__add_source(vertex, core, link)

    def add_machine_sources_for_target(
            self, core, link, source_vertices, partition_id):
        """ Add a set of machine vertices that target a given core or link

        :param core: The core to target with the sources or None if no core
        :type core: int or None
        :param link: The link to target with the sources or None if no link
        :type link: int or None
        :param source_vertices: A list of sources which target something here
        :type source_vertices: list(ApplicationVertex or MachineVertex)
        :param str partition_id: The partition of the sources
        """
        for vertex in source_vertices:
            if isinstance(vertex, ApplicationVertex):
                if vertex in self.__targets_by_source:
                    self.__replace_app_vertex(vertex, partition_id)
                self.__add_m_vertices(vertex, partition_id, core, link)
            else:
                if vertex.app_vertex in self.__targets_by_source:
                    self.__replace_app_vertex(vertex.app_vertex, partition_id)
                self.__add_source(vertex, core, link)

    def __is_m_vertex(self, vertex, partition_id):
        for m_vert in vertex.splitter.get_out_going_vertices(partition_id):
            if m_vert in self.__targets_by_source:
                return True
        return False

    def __replace_app_vertex(self, vertex, partition_id):
        cores = self.__targets_by_source[vertex][0]
        links = self.__targets_by_source[vertex][1]
        del self.__targets_by_source[vertex]
        for m_vertex in vertex.splitter.get_out_going_vertices(partition_id):
            self.__targets_by_source[m_vertex] = (cores, links)

    def __add_m_vertices(self, vertex, partition_id, core, link):
        for m_vertex in vertex.splitter.get_out_going_vertices(partition_id):
            self.__add_source(m_vertex, core, link)

    def __add_source(self, source, core, link):
        if core is not None:
            self.__targets_by_source[source][0].append(core)
        if link is not None:
            self.__targets_by_source[source][1].append(link)

    @property
    def targets_by_source(self):
        """ Get a list of (source, (list of cores, list of links)) to target

        :rtype: tuple(MachineVertex or ApplicationVertex,
                      tuple(list(int), list(int)))
        """
        return self.__targets_by_source.items()

    def get_targets_for_source(self, vertex):
        """ Get the cores and links for a specific source

        :return: tuple(list of cores, list of links)
        :rtype: tuple(list(int), list(int))
        """
        return vertex, self.__targets_by_source[vertex]


def route_application_graph():
    """ Route an application graph
    """
    routing_tables = MulticastRoutingTableByPartition()

    partitions = get_app_partitions()
    machine = PacmanDataView.get_machine()
    # Now go through the app edges and route app vertex by app vertex
    progress = ProgressBar(len(partitions), "Routing")
    for partition in progress.over(partitions):
        # Store the source vertex of the partition
        source = partition.pre_vertex

        # Pick a place within the source that we can route from.  Note that
        # this might not end up being the actual source in the end.
        source_mappings = _get_outgoing_mapping(
            source, partition.identifier)

        # No source mappings?  Nothing to route then!
        if not source_mappings:
            continue

        source_xy = next(iter(source_mappings.keys()))
        # Get all source chips coordinates
        all_source_xys = _get_all_xys(source)

        # Keep track of the source edge chips
        source_edge_xys = set()

        # Keep track of which chips (xys) we have visited with routes for this
        # partition to ensure no looping
        routes = dict()

        # Keep track of cores or links to target on specific chips (xys)
        targets = defaultdict(_Targets)

        # Remember if we see a self-connection
        self_connected = False
        self_xys = set()

        for edge in partition.edges:
            # Store the target vertex
            target = edge.post_vertex

            # If not self-connected
            if source != target:

                # Find all coordinates for chips (xy) that are in the target
                target_xys = _get_all_xys(target)

                # Pick one to actually use as a target
                target_xy = _find_target_xy(
                    target_xys, routes, source_mappings)

                # Make a route between source and target, without any source
                # or target chips in it
                source_edge_xy, target_edge_xy = _route_pre_to_post(
                    source_xy, target_xy, routes, machine,
                    f"Source to Target ({target.label})", all_source_xys,
                    target_xys)

                # Add all the targets for the route
                target_vertices = \
                    target.splitter.get_source_specific_in_coming_vertices(
                        source, partition.identifier)
                real_target_xys = set()
                for tgt, srcs in target_vertices:
                    xy, (_vertex, core, link) = vertex_xy_and_route(tgt)
                    if xy in source_mappings:
                        targets[xy].add_machine_sources_for_target(
                            core, link, srcs, partition.identifier)
                    else:
                        targets[xy].add_sources_for_target(
                            core, link, srcs, partition.identifier)

                    real_target_xys.add(xy)

                # Route from target edge chip to all the targets
                _route_to_xys(
                    target_edge_xy, target_xys, machine, routes,
                    real_target_xys, "Target to Targets")

                # If the start of the route is still part of the source vertex
                # chips, add it
                if source_edge_xy in source_mappings:
                    source_edge_xys.add(source_edge_xy)

            # If self-connected
            else:
                self_connected = True

                # If self-connected, add the targets of the sources
                target_vertices = \
                    source.splitter.get_source_specific_in_coming_vertices(
                        source, partition.identifier)
                for tgt, srcs in target_vertices:
                    xy, (_vertex, core, link) = vertex_xy_and_route(tgt)
                    targets[xy].add_machine_sources_for_target(
                        core, link, srcs, partition.identifier)
                    self_xys.add(xy)

        # Deal with internal multicast partitions
        internal = source.splitter.get_internal_multicast_partitions()
        if internal:
            self_connected = True
            for in_part in internal:
                src = in_part.pre_vertex
                for edge in in_part.edges:
                    tgt = edge.post_vertex
                    xy, (_vertex, core, link) = vertex_xy_and_route(tgt)
                    targets[xy].add_machine_sources_for_target(
                        core, link, [src], in_part.identifier)
                    self_xys.add(xy)

        # Make the real routes from source edges to targets
        for source_edge_xy in source_edge_xys:
            # Make sure that we add the machine sources on the source edge chip
            if source_edge_xy not in targets:
                edge_targets = _Targets()
                for source_xy in source_mappings:
                    for vertex, _p, _l in source_mappings[source_xy]:
                        edge_targets.ensure_source(vertex)
                targets[source_edge_xy] = edge_targets

            _convert_a_route(
                routing_tables, source, partition.identifier, None, None,
                routes[source_edge_xy], targets=targets,
                ensure_all_source=True)

        # Now make the routes from actual sources to source edges
        if self_connected:
            for xy in source_mappings:
                source_routes = dict()
                _route_to_xys(
                    xy, all_source_xys, machine, source_routes,
                    source_edge_xys.union(self_xys),
                    "Sources to Source (self)")
                for vertex, processor, link in source_mappings[xy]:
                    _convert_a_route(
                        routing_tables, vertex, partition.identifier,
                        processor, link, source_routes[xy], targets=targets,
                        use_source_for_targets=True)
        else:
            for xy in source_mappings:
                source_routes = dict()
                _route_to_xys(
                    xy, all_source_xys, machine, source_routes,
                    source_edge_xys, "Sources to source")
                for vertex, processor, link in source_mappings[xy]:
                    _convert_a_route(
                        routing_tables, vertex, partition.identifier,
                        processor, link, source_routes[xy])

    # Return the routing tables
    return routing_tables


def _find_target_xy(target_xys, routes, source_mappings):
    """

    :param set(tuple(int, int)) target_xys:
    :param routes:
    :param dict(tuple(int, int), list) outgoing_mappings:
    :return:
    :rtype: tuple(int, int)
    """
    for xy in target_xys:
        if xy in source_mappings:
            return xy
    for xy in target_xys:
        if xy in routes:
            return xy
    return xy


def _get_outgoing_mapping(app_vertex, partition_id):
    """
    Gets a Mapping from xy sources to a list of (vertex, the vertex,
        processor and link to follow to get to the vertex

    For each tuple in the list either processor or link will be None

    :param app_vertex:
    :param partition_id:
    :rtype: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
             tuple(MachineVertex, None, int)))
    """
    outgoing_mapping = defaultdict(list)
    for m_vertex in app_vertex.splitter.get_out_going_vertices(partition_id):
        xy, route = vertex_xy_and_route(m_vertex)
        outgoing_mapping[xy].append(route)
    for in_part in app_vertex.splitter.get_internal_multicast_partitions():
        if in_part.identifier == partition_id:
            xy, route = vertex_xy_and_route(in_part.pre_vertex)
            outgoing_mapping[xy].append(route)
    return outgoing_mapping


def _get_all_xys(app_vertex):
    """
    Gets the list of all the xy coordinates the vertexes machine vertices
        are placed on

    :param app_vertex:
    :rtype: set(tuple(int, int))
    """
    return {vertex_xy(m_vertex)
            for m_vertex in app_vertex.machine_vertices}


def _route_to_xys(first_xy, all_xys, machine, routes, targets, label):
    """

    :param tuple(int, int) first_xy:
    :param list(tuple(int, int)) all_xys:
    :param machine:
    :param routes:
    :param targets:
    :param label:
    """
    # Keep a queue of xy to visit, list of (parent xy, link from parent)
    xys_to_explore = deque([(first_xy, list())])
    visited = set()
    targets_to_visit = set(targets)
    while xys_to_explore:
        xy, path = xys_to_explore.popleft()
        if xy in targets_to_visit:
            targets_to_visit.remove(xy)
        if xy in visited:
            continue
        visited.add(xy)

        # If we have reached a xy that has already been routed to,
        # cut the path off here
        if xy in routes:
            path = list()

        # If we have reached a target, add the path to the routes
        elif xy in targets:
            routes[xy] = RoutingTree(xy, label)
            last_route = routes[xy]
            for parent, link in reversed(path):
                if parent not in routes:
                    routes[parent] = RoutingTree(parent, label)
                routes[parent].append_child((link, last_route))
                last_route = routes[parent]

            # The path can be reset from here as we have already routed here
            path = list()

        for link in range(6):
            x, y = xy
            if machine.is_link_at(x, y, link):
                next_xy = machine.xy_over_link(x, y, link)
                if _is_open_chip(next_xy, all_xys, visited, machine):
                    new_path = list(path)
                    new_path.append((xy, link))
                    xys_to_explore.append((next_xy, new_path))
    # Sanity check
    if targets_to_visit:
        raise Exception(
            f"Failed to visit all targets {targets} from {first_xy}: "
            f" Not visited {targets_to_visit}")


def _is_open_chip(xy, xys, visited, machine):
    """

    :param tuple(int, int) xy:
    :param list(tuple(int, int) xys: List of legal xys
    :param set(tuple(int, int) visited:
    :param machine:
    :return: True if the cooridnates point to an existing Chip not yet visited
    """
    return xy in xys and xy not in visited and machine.is_chip_at(*xy)


def _route_pre_to_post(
        source_xy, dest_xy, routes, machine, label, all_source_xy,
        target_xys):
    """

    :param tuple(int, int) source_xy:
    :param tuple(int, int) dest_xy:
    :param routes:
    :param machine:
    :param str label:
    :param set(tuple(int, int)) all_source_xy:
    :param  set(tuple(int, int)) target_xys:
    :return: the pre and post xy coordinates
    :rtype: tuple(tuple(int,int), tuple(int, int))
    """
    # Find a route from source to target
    vector = machine.get_vector(source_xy, dest_xy)
    nodes_direct = longest_dimension_first(vector, source_xy)

    # Route around broken links and chips
    nodes_fixed = _path_without_errors(source_xy, nodes_direct, machine)

    # Start from the end and move backwards until we find a chip
    # in the source group, or a already in the route
    nodes = nodes_fixed
    route_pre = source_xy
    for i, (_direction, (x, y)) in reversed(list(enumerate(nodes))):
        if _in_group((x, y), all_source_xy) or (x, y) in routes:
            nodes = nodes[i + 1:]
            route_pre = (x, y)
            break

    # If we found one not in the route, create a new entry for it
    if route_pre not in routes:
        routes[route_pre] = RoutingTree(route_pre, label)

    # Start from the start and move forwards until we find a chip in
    # the target group
    route_post = dest_xy
    for i, (_direction, (x, y)) in enumerate(nodes):
        if (x, y) in target_xys:
            nodes = nodes[:i + 1]
            route_post = (x, y)
            break

    # Convert nodes to routes and add to existing routes
    source_route = routes[route_pre]
    for direction, dest_node in nodes:
        if dest_node in routes:
            _print_path(routes[source_xy])
            print(f"Direct path from {source_xy} to {dest_xy}: {nodes_direct}")
            print(f"Avoiding down chips: {nodes_fixed}")
            print(f"Trimmed path is from {route_pre} to {route_post}: {nodes}")
            raise Exception(
                f"Somehow node {dest_node} already in routes with label"
                f" {routes[dest_node].label}")
        dest_route = RoutingTree(dest_node, label)
        routes[dest_node] = dest_route
        source_route.append_child((direction, dest_route))
        source_route = dest_route

    return route_pre, route_post


def _path_without_errors(source_xy, nodes, machine):
    """

    :param tuple(int, int) source_xy:
    :param  list(tuple(int,tuple(int, int))) nodes:
    :param machine:
    :rtype: list(tuple(int,int))
    """
    c_xy = source_xy
    pos = 0
    new_nodes = list()
    while pos < len(nodes):

        # While the route is working, move forwards and copy
        while (pos < len(nodes) and _is_ok(c_xy, nodes[pos], machine)):
            new_nodes.append(nodes[pos])
            c_xy = _xy(nodes[pos])
            pos += 1

        # While the route is broken, find the next working bit
        next_pos = pos
        n_xy = c_xy
        while (next_pos < len(nodes) and not _is_ok(
                n_xy, nodes[next_pos], machine)):
            n_xy = _xy(nodes[next_pos])
            next_pos += 1

        # If there is a broken bit, fix it
        if next_pos != pos:
            new_nodes.extend(_find_path(c_xy, n_xy, machine))
        c_xy = n_xy
        pos = next_pos
    return _path_without_loops(source_xy, new_nodes)


def _path_without_loops(start_xy, nodes):
    """

    :param tuple(int, int) start_xy:
    :param list(tuple(int,int)) nodes:
    :rtype: list(tuple(int,int))
    """
    seen_nodes = {start_xy: 0}
    i = 0
    while i < len(nodes):
        _, nxt = nodes[i]
        if nxt in seen_nodes:
            last_seen = seen_nodes[nxt]
            del nodes[last_seen:i + 1]
            i = last_seen
        else:
            i += 1
            seen_nodes[nxt] = i
    return nodes


def _is_ok(xy, node, machine):
    """

    :param tuple(int, int) xy:
    :param tuple(int,tuple(int, int)) node:
    :param machine:
    :return:
    """
    c_x, c_y = xy
    direction, (n_x, n_y) = node
    if machine.is_link_at(c_x, c_y, direction):
        if machine.is_chip_at(n_x, n_y):
            return True
    return False


def _xy(node):
    _, (x, y) = node
    return (x, y)


def _find_path(source_xy, target_xy, machine):
    xys_to_explore = deque([(source_xy, list())])
    visited = set()
    while xys_to_explore:
        xy, path = xys_to_explore.popleft()
        if xy in visited:
            continue
        visited.add(xy)

        # If we have reached a target, add the path to the routes
        if xy == target_xy:
            return path

        for link in range(6):
            x, y = xy
            if machine.is_link_at(x, y, link):
                next_xy = machine.xy_over_link(x, y, link)
                if _is_open_chip(next_xy, [next_xy], visited, machine):
                    new_path = list(path)
                    new_path.append((link, next_xy))
                    xys_to_explore.append((next_xy, new_path))
    raise Exception(f"No path from {source_xy} to {target_xy}")


def _in_group(item, group):
    if group is None:
        return False
    return item in group


def _convert_a_route(
        routing_tables, source_vertex, partition_id, first_incoming_processor,
        first_incoming_link, first_route, targets=None,
        use_source_for_targets=False, ensure_all_source=False):
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
    :param targets:
        Targets for each chip.  When present for a chip, the route links and
        cores are added to each entry in the targets.
    :type targets: dict(tuple(int,int),_Targets) or None
    :param bool use_source_for_targets:
        If true, targets for the given source_vertex will be requested;
        If false all targets for matching chips will be used.
    :param bool ensure_all_source:
        If true, ensures that all machine vertices of the source app vertex
        are covered in routes that continue forward
    """

    to_process = [(first_incoming_processor, first_incoming_link, first_route)]
    while to_process:
        incoming_processor, incoming_link, route = to_process.pop()
        x, y = route.chip

        processor_ids = list()
        link_ids = list()
        for (route, next_hop) in route.children:
            if route is not None:
                link_ids.append(route)
                next_incoming_link = (route + 3) % 6
            if next_hop is not None:
                to_process.append((None, next_incoming_link, next_hop))

        if targets is not None and (x, y) in targets:
            chip_targets = targets[x, y]
            if use_source_for_targets:
                targets_by_source = [
                    chip_targets.get_targets_for_source(source_vertex)]
            else:
                targets_by_source = chip_targets.targets_by_source

            # We must ensure that all machine vertices of an app vertex
            # are covered!
            machine_vertex_sources = set()
            app_vertex_source = False
            for (source, (add_cores, add_links)) in targets_by_source:
                if isinstance(source, ApplicationVertex):
                    app_vertex_source = True
                else:
                    machine_vertex_sources.add(source)
                entry = MulticastRoutingTableByPartitionEntry(
                    link_ids + add_links, processor_ids + add_cores,
                    incoming_processor, incoming_link)
                _add_routing_entry(
                    first_route, routing_tables, entry, x, y, source,
                    partition_id)

            # Now check the coverage of Application and machine vertices
            if ensure_all_source and not app_vertex_source:
                for m_vert in source_vertex.splitter.get_out_going_vertices(
                        partition_id):
                    if m_vert not in machine_vertex_sources:
                        entry = MulticastRoutingTableByPartitionEntry(
                            link_ids, processor_ids, incoming_processor,
                            incoming_link)
                        _add_routing_entry(
                            first_route, routing_tables, entry, x, y, m_vert,
                            partition_id)
        else:
            entry = MulticastRoutingTableByPartitionEntry(
                link_ids, processor_ids, incoming_processor, incoming_link)
            _add_routing_entry(
                first_route, routing_tables, entry, x, y, source_vertex,
                partition_id)


def _add_routing_entry(
        first_route, routing_tables, entry, x, y, source, partition_id):
    try:
        routing_tables.add_path_entry(entry, x, y, source, partition_id)
    except Exception as e:
        print(f"Error adding route: {e}")
        _print_path(first_route)
        raise e


def _print_path(first_route):
    to_process = [("", None, first_route)]
    last_is_leaf = False
    line = ""
    while to_process:
        prefix, link, route = to_process.pop()

        if last_is_leaf:
            line += prefix

        to_add = ""
        if link is not None:
            to_add += f" -> {link} -> "
        to_add += f"{route.chip} ({route.label})"
        line += to_add
        prefix += " " * len(to_add)

        if route.is_leaf:
            # This is a leaf
            last_is_leaf = True
            print(line)
            line = ""
        else:
            last_is_leaf = False
            for direction, next_route in route.children:
                to_process.append((prefix, direction, next_route))
