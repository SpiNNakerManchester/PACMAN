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
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first, get_app_partitions, vertex_xy,
    vertex_chip_and_route)
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree
from pacman.model.graphs.application import ApplicationVertex
from collections import deque, defaultdict
from spinn_utilities.progress_bar import ProgressBar


class _Targets(object):
    """ A set of targets to be added to a route on a chip
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


def route_application_graph(machine, app_graph, placements):
    """ Route an application graph
    """
    routing_tables = MulticastRoutingTableByPartition()

    partitions = get_app_partitions(app_graph)

    # Now go through the app edges and route app vertex by app vertex
    progress = ProgressBar(len(partitions), "Routing")
    for partition in progress.over(partitions):
        # Store the source vertex of the partition
        source = partition.pre_vertex

        # Pick a place within the source that we can route from.  Note that
        # this might not end up being the actual source in the end.
        source_chip, source_chips = _get_outgoing_chips(
            partition.pre_vertex, partition.identifier, placements, machine)

        # No source chips?  Nothing to route then!
        if source_chip is None:
            continue

        # Get all source chips
        all_source_chips = _get_all_chips(source, placements, machine)

        # Keep track of the source edge chips
        source_edge_chips = set()

        # Keep track of which chips we have visited with routes for this
        # partition to ensure no looping
        routes = dict()

        # Keep track of cores or links to target on specific chips
        targets = defaultdict(_Targets)

        # Remember if we see a self-connection
        self_connected = False
        self_chips = set()

        for edge in partition.edges:
            # Store the target vertex
            target = edge.post_vertex

            # If not self-connected
            if source != target:

                # Find all chips that are in the target
                target_chips = _get_all_chips(target, placements, machine)

                # Pick one to actually use as a target
                target_chip = _find_target_chip(
                    target_chips, routes, source_chips)

                # Make a route between source and target, without any source
                # or target chips in it
                source_edge_chip, target_edge_chip = _route_pre_to_post(
                    source_chip, target_chip, routes, machine,
                    f"Source to Target ({target.label})", all_source_chips,
                    target_chips)

                # Add all the targets for the route
                target_vertices = \
                    target.splitter.get_source_specific_in_coming_vertices(
                        source, partition.identifier)
                real_target_chips = set()
                for tgt, srcs in target_vertices:
                    xy, (_vertex, core, link) = vertex_chip_and_route(
                        tgt, placements, machine)
                    if xy in source_chips:
                        targets[xy].add_machine_sources_for_target(
                            core, link, srcs, partition.identifier)
                    else:
                        targets[xy].add_sources_for_target(
                            core, link, srcs, partition.identifier)

                    real_target_chips.add(xy)

                # Route from target edge chip to all the targets
                _route_to_target_chips(
                    target_edge_chip, target_chips, machine, routes,
                    real_target_chips, "Target to Targets")

                # If the start of the route is still part of the source vertex
                # chips, add it
                if source_edge_chip in source_chips:
                    source_edge_chips.add(source_edge_chip)

            # If self-connected
            else:
                self_connected = True

                # If self-connected, add the targets of the sources
                target_vertices = \
                    source.splitter.get_source_specific_in_coming_vertices(
                        source, partition.identifier)
                for tgt, srcs in target_vertices:
                    xy, (_vertex, core, link) = vertex_chip_and_route(
                        tgt, placements, machine)
                    targets[xy].add_machine_sources_for_target(
                        core, link, srcs, partition.identifier)
                    self_chips.add(xy)

        # Deal with internal multicast partitions
        internal = source.splitter.get_internal_multicast_partitions()
        if internal:
            self_connected = True
            for in_part in internal:
                src = in_part.pre_vertex
                for edge in in_part.edges:
                    tgt = edge.post_vertex
                    xy, (_vertex, core, link) = vertex_chip_and_route(
                        tgt, placements, machine)
                    targets[xy].add_machine_sources_for_target(
                        core, link, [src], in_part.identifier)
                    self_chips.add(xy)

        # Make the real routes from source edges to targets
        for source_edge_chip in source_edge_chips:
            # Make sure that we add the machine sources on the source edge chip
            if source_edge_chip not in targets:
                edge_targets = _Targets()
                for source_chip in source_chips:
                    for vertex, _p, _l in source_chips[source_chip]:
                        edge_targets.ensure_source(vertex)
                targets[source_edge_chip] = edge_targets

            _convert_a_route(
                routing_tables, source, partition.identifier, None, None,
                routes[source_edge_chip], targets=targets,
                ensure_all_source=True)

        # Now make the routes from actual sources to source edges
        if self_connected:
            for chip in source_chips:
                source_routes = dict()
                _route_to_target_chips(
                    chip, all_source_chips, machine, source_routes,
                    source_edge_chips.union(self_chips),
                    "Sources to Source (self)")
                for vertex, processor, link in source_chips[chip]:
                    _convert_a_route(
                        routing_tables, vertex, partition.identifier,
                        processor, link, source_routes[chip], targets=targets,
                        use_source_for_targets=True)
        else:
            for chip in source_chips:
                source_routes = dict()
                _route_to_target_chips(
                    chip, all_source_chips, machine, source_routes,
                    source_edge_chips, "Sources to source")
                for vertex, processor, link in source_chips[chip]:
                    _convert_a_route(
                        routing_tables, vertex, partition.identifier,
                        processor, link, source_routes[chip])

    # Return the routing tables
    return routing_tables


def _find_target_chip(target_chips, routes, source_chips):
    for chip in target_chips:
        if chip in source_chips:
            return chip
    for chip in target_chips:
        if chip in routes:
            return chip
    return chip


def _get_outgoing_chips(app_vertex, partition_id, placements, machine):
    vertex_chips = defaultdict(list)
    for m_vertex in app_vertex.splitter.get_out_going_vertices(partition_id):
        xy, route = vertex_chip_and_route(m_vertex, placements, machine)
        vertex_chips[xy].append(route)
    for in_part in app_vertex.splitter.get_internal_multicast_partitions():
        if in_part.identifier == partition_id:
            xy, route = vertex_chip_and_route(
                in_part.pre_vertex, placements, machine)
            vertex_chips[xy].append(route)
    if not vertex_chips:
        return None, None
    first_chip = next(iter(vertex_chips.keys()))
    return (first_chip, vertex_chips)


def _get_all_chips(app_vertex, placements, machine):
    return {vertex_xy(m_vertex, placements, machine)
            for m_vertex in app_vertex.machine_vertices}


def _route_to_target_chips(first_chip, chips, machine, routes, targets, label):
    # Keep a queue of chip to visit, list of (parent chip, link from parent)
    chips_to_explore = deque([(first_chip, list())])
    visited = set()
    targets_to_visit = set(targets)
    while chips_to_explore:
        chip, path = chips_to_explore.popleft()
        if chip in targets_to_visit:
            targets_to_visit.remove(chip)
        if chip in visited:
            continue
        visited.add(chip)

        # If we have reached a chip that has already been routed to,
        # cut the path off here
        if chip in routes:
            path = list()

        # If we have reached a target, add the path to the routes
        elif chip in targets:
            routes[chip] = RoutingTree(chip, label)
            last_route = routes[chip]
            for parent, link in reversed(path):
                if parent not in routes:
                    routes[parent] = RoutingTree(parent, label)
                routes[parent].append_child((link, last_route))
                last_route = routes[parent]

            # The path can be reset from here as we have already routed here
            path = list()

        for link in range(6):
            x, y = chip
            if machine.is_link_at(x, y, link):
                next_chip = machine.xy_over_link(x, y, link)
                if _is_open_chip(next_chip, chips, visited, machine):
                    new_path = list(path)
                    new_path.append((chip, link))
                    chips_to_explore.append((next_chip, new_path))
    # Sanity check
    if targets_to_visit:
        raise Exception(
            f"Failed to visit all targets {targets} from {first_chip}: "
            f" Not visited {targets_to_visit}")


def _is_open_chip(chip, chips, visited, machine):
    x, y = chip
    is_in_range = chips is None or chip in chips
    return is_in_range and chip not in visited and machine.is_chip_at(x, y)


def _route_pre_to_post(
        source_xy, dest_xy, routes, machine, label, source_group=None,
        target_group=None):
    # Find a route from source to target
    vector = machine.get_vector(source_xy, dest_xy)
    nodes_direct = longest_dimension_first(vector, source_xy, machine)

    # Route around broken links and chips
    nodes_fixed = _path_without_errors(source_xy, nodes_direct, machine)

    # Start from the end and move backwards until we find a chip
    # in the source group, or a already in the route
    nodes = nodes_fixed
    route_pre = source_xy
    for i, (_direction, (x, y)) in reversed(list(enumerate(nodes))):
        if _in_group((x, y), source_group) or (x, y) in routes:
            nodes = nodes[i + 1:]
            route_pre = (x, y)
            break

    # If we found one not in the route, create a new entry for it
    if route_pre not in routes:
        routes[route_pre] = RoutingTree(route_pre, label)

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


def _is_ok(xy, node, mac):
    c_x, c_y = xy
    direction, (n_x, n_y) = node
    if mac.is_link_at(c_x, c_y, direction) and mac.is_chip_at(n_x, n_y):
        return True
    return False


def _xy(node):
    _, (x, y) = node
    return (x, y)


def _find_path(source_xy, target_xy, machine):
    chips_to_explore = deque([(source_xy, list())])
    visited = set()
    while chips_to_explore:
        chip, path = chips_to_explore.popleft()
        if chip in visited:
            continue
        visited.add(chip)

        # If we have reached a target, add the path to the routes
        if chip == target_xy:
            return path

        for link in range(6):
            x, y = chip
            if machine.is_link_at(x, y, link):
                next_chip = machine.xy_over_link(x, y, link)
                if _is_open_chip(next_chip, None, visited, machine):
                    new_path = list(path)
                    new_path.append((link, next_chip))
                    chips_to_explore.append((next_chip, new_path))
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
