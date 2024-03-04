# Copyright (c) 2021 The University of Manchester
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

from collections import deque, defaultdict
from typing import (
    Deque, Dict, Iterable, List, Optional, Set, Tuple, Union)
from typing_extensions import TypeAlias
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.typing.coords import XY
from spinn_machine import Machine
from pacman.data import PacmanDataView
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    longest_dimension_first, get_app_partitions, vertex_xy,
    vertex_xy_and_route)
from pacman.utilities.algorithm_utilities.routing_tree import RoutingTree
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex, MulticastEdgePartition
from pacman.model.graphs import AbstractEdgePartition

_AnyVertex: TypeAlias = Union[ApplicationVertex, MachineVertex]
_Node: TypeAlias = Tuple[int, XY]
_OptInt: TypeAlias = Optional[int]
_MappedSrc: TypeAlias = Tuple[_AnyVertex, _OptInt, _OptInt]


class _Targets(object):
    """
    A set of targets to be added to a route on a chip at coordinates (x,y).
    """
    __slots__ = ("__targets_by_source", )

    def __init__(self) -> None:
        self.__targets_by_source: Dict[
            _AnyVertex, Tuple[List[int], List[int]]] = defaultdict(
                lambda: (list(), list()))

    def ensure_source(self, source_vertex: _AnyVertex):
        """
        Ensure that a source exists, even if it targets nothing.

        :param source_vertex: The vertex to ensure exists
        :type source_vertex: ApplicationVertex or MachineVertex
        """
        if source_vertex not in self.__targets_by_source:
            self.__targets_by_source[source_vertex] = (list(), list())

    def add_sources_for_target(
            self, core: _OptInt, link: _OptInt,
            source_vertices: Iterable[_AnyVertex], partition_id: str):
        """
        Add a set of vertices that target a given core or link.

        :param core: The core to target with the sources or `None` if no core
        :type core: int or None
        :param link: The link to target with the sources or `None` if no link
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
            self, core: _OptInt, link: _OptInt,
            source_vertices: Iterable[_AnyVertex], partition_id: str):
        """
        Add a set of machine vertices that target a given core or link.

        :param core: The core to target with the sources or `None` if no core
        :type core: int or None
        :param link: The link to target with the sources or `None` if no link
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

    def __is_m_vertex(
            self, vertex: ApplicationVertex, partition_id: str) -> bool:
        """
        :param ApplicationVertex vertex:
        :param str partition_id:
        :rtype: bool
        """
        if not vertex.has_splitter:
            return False
        return any(
            vtx in self.__targets_by_source
            for vtx in vertex.splitter.get_out_going_vertices(partition_id))

    def __replace_app_vertex(
            self, vertex: ApplicationVertex, partition_id: str):
        """
        :param ApplicationVertex vertex:
        :param str partition_id:
        """
        cores = self.__targets_by_source[vertex][0]
        links = self.__targets_by_source[vertex][1]
        del self.__targets_by_source[vertex]
        for vtx in vertex.splitter.get_out_going_vertices(partition_id):
            self.__targets_by_source[vtx] = (cores, links)

    def __add_m_vertices(
            self, vertex: ApplicationVertex, partition_id: str,
            core: _OptInt, link: _OptInt):
        """
        :param ApplicationVertex vertex:
        :param str partition_id:
        :param int core:
        :param int link:
        """
        for vtx in vertex.splitter.get_out_going_vertices(partition_id):
            self.__add_source(vtx, core, link)

    def __add_source(self, source: _AnyVertex, core: _OptInt, link: _OptInt):
        """
        :param AbstractVertex source:
        :param int core:
        :param int link:
        """
        tgt = self.__targets_by_source[source]
        if core is not None:
            tgt[0].append(core)
        if link is not None:
            tgt[1].append(link)

    @property
    def targets_by_source(self) -> Iterable[
            Tuple[_AnyVertex, Tuple[List[int], List[int]]]]:
        """
        List of (source, (list of cores, list of links)) to target.

        :rtype: tuple(MachineVertex or ApplicationVertex,
                      tuple(list(int), list(int)))
        """
        return self.__targets_by_source.items()

    def get_targets_for_source(self, vertex: _AnyVertex) -> Tuple[
            _AnyVertex, Tuple[List[int], List[int]]]:
        """
        Get the cores and links for a specific source.

        :return: tuple(list of cores, list of links)
        :rtype: tuple(list(int), list(int))
        """
        return vertex, self.__targets_by_source[vertex]


def route_application_graph() -> MulticastRoutingTableByPartition:
    """
    Route the current application graph.
    """
    routing_tables = MulticastRoutingTableByPartition()

    partitions = get_app_partitions()
    machine = PacmanDataView.get_machine()
    # Now go through the app edges and route app vertex by app vertex
    progress = ProgressBar(len(partitions), "Routing")
    for partition in progress.over(partitions):
        # Store the source vertex of the partition
        source: ApplicationVertex = partition.pre_vertex

        # Pick a place within the source that we can route from.  Note that
        # this might not end up being the actual source in the end.
        source_mappings = _get_outgoing_mapping(source, partition.identifier)

        # No source mappings?  Nothing to route then!
        if not source_mappings:
            continue

        source_xy = next(iter(source_mappings.keys()))
        # Get all source chips coordinates
        all_source_xys = _get_all_xys(source)

        # Keep track of the source edge chips
        source_edge_xys: Set[XY] = set()

        # Keep track of which chips (xys) we have visited with routes for this
        # partition to ensure no looping
        routes: Dict[XY, RoutingTree] = dict()

        # Keep track of cores or links to target on specific chips (xys)
        targets: Dict[XY, _Targets] = defaultdict(_Targets)

        # Remember if we see a self-connection
        self_connected = False
        self_xys: Set[XY] = set()

        for edge in partition.edges:
            # Store the target vertex
            target = edge.post_vertex

            # If not self-connected
            if source != target:
                _route_source_to_target(
                    machine, source, source_xy, all_source_xys,
                    source_mappings, source_edge_xys, target, targets,
                    partition, routes)
            # If self-connected
            else:
                self_connected = True
                _route_source_to_source(source, partition, targets, self_xys)

        # Deal with internal multicast partitions
        internal = source.splitter.get_internal_multicast_partitions()
        if internal:
            self_connected = True
            _route_internal(internal, targets, self_xys)

        # Make the real routes from source edges to targets
        _make_source_to_target_routes(
            source, partition, source_edge_xys, source_mappings, targets,
            routing_tables, routes)

        # Now make the routes from actual sources to source edges
        if self_connected:
            _make_source_to_source_routes(
                all_source_xys, source_edge_xys, self_xys, source_mappings,
                machine, partition, routing_tables, targets)
        else:
            _make_source_to_source_edge_routes(
                all_source_xys, source_edge_xys, source_mappings, machine,
                partition, routing_tables)

    # Return the routing tables
    return routing_tables


def _route_source_to_target(
        machine: Machine, source: ApplicationVertex,
        source_xy: XY, all_source_xys: Set[XY],
        source_mappings: Dict[XY, List[_MappedSrc]],
        source_edge_xys: Set[XY], target: ApplicationVertex,
        targets: Dict[XY, _Targets],
        partition: AbstractEdgePartition,
        routes: Dict[XY, RoutingTree]):
    """
    Route from a source to a single application vertex target that is not
    the same as the source.

    :param Machine machine: The machine to route on
    :param ApplicationVertex source: The source application vertex
    :param tuple(int,int) source_xy: A chip chosen in the source to route from
    :param set(tuple(int,int) all_source_xys: All source chips
    :param source_mappings: The sources mapped to their routes
    :type source_mappings: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
        tuple(MachineVertex, None, int)))
    :param set(tuple(int,int)) source_edge_xys:
        Set of chips that routes are currently going outward from the source
        (updated here)
    :param ApplicationVertex target: The target application vertex
    :param dict(tuple(int,int),_Targets) targets:
        The set of actual targets to be added on chips (updated here)
    :param AbstractEdgePartition partition: The partition being routed
    :param dict(tuple(int,int), RoutingTree) routes:
        The routes made by chip (updated here)
    """
    # Get which vertices are targeted by the source
    target_vertices = target.splitter.get_source_specific_in_coming_vertices(
        source, partition.identifier)

    # Add all the targets for the route
    real_target_xys: Set[XY] = set()
    for tgt, srcs in target_vertices:
        xy, (_vertex, core, link) = vertex_xy_and_route(tgt)
        if xy in source_mappings:
            targets[xy].add_machine_sources_for_target(
                core, link, srcs, partition.identifier)
        else:
            targets[xy].add_sources_for_target(
                core, link, srcs, partition.identifier)

        real_target_xys.add(xy)

    target_xys: Set[XY]
    # If there is just one real target, use that directly
    if len(real_target_xys) == 1:
        target_xys = set([xy])
        target_xy = xy
        overlaps = None
    else:
        # Find all coordinates for chips (xy) that are in the target
        target_xys = _get_all_xys(target)

        # Pick one to actually use as a target
        target_xy, overlaps = _find_target_xy(
            target_xys, routes, source_mappings)

    # Make a route between source and target, without any source
    # or target chips in it
    source_edge_xy, target_edge_xy = _route_pre_to_post(
        source_xy, target_xy, routes, machine,
        f"Source to Target ({target.label})", all_source_xys,
        target_xys)

    if not overlaps:
        _route_single_source_to_target(
            machine, source_edge_xys, source_edge_xy, source_mappings,
            target_edge_xy, target_xys, real_target_xys, routes)
    else:
        _route_multiple_source_to_target(
            machine, source_edge_xys, target_edge_xy, target_xys,
            real_target_xys, routes, overlaps)


def _route_single_source_to_target(
        machine: Machine, source_edge_xys: Set[XY], source_edge_xy: XY,
        source_mappings: Dict[XY, List[_MappedSrc]], target_edge_xy: XY,
        target_xys: Set[XY], real_target_xys: Set[XY],
        routes: Dict[XY, RoutingTree]):
    """
    Route from a single source connection point to all targets from the
    target edge chip.

    :param Machine machine: The machine to route on
    :param set(tuple(int,int)) source_edge_xys:
        Set of chips that routes are currently going outward from the source
        (updated here)
    :param tuple(int,int) source_edge_xy:
        The x and y coordinate of the actual source edge chip to route from
    :param source_mappings: The sources mapped to their routes
    :type source_mappings: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
        tuple(MachineVertex, None, int)))
    :param tuple(int,int) target_edge_xy:
        The x and y coordinate of the actual target edge chip to route to
    :param list(tuple(int,int)) target_xys: The chips in the target
    :param set(tuple(int,int)) real_target_xys:
        The chips in the target that something in the source actually targets
    :param dict(tuple(int,int), RoutingTree) routes:
        The routes already made and to add to (updated here)
    """
    # Route from target edge chip to all the targets
    _route_to_xys(
        target_edge_xy, target_xys, machine, routes,
        real_target_xys, "Target to Targets")

    # If the start of the route is still part of the source vertex
    # chips, add it
    if source_edge_xy in source_mappings:
        source_edge_xys.add(source_edge_xy)


def _route_multiple_source_to_target(
        machine: Machine, source_edge_xys: Set[XY], target_edge_xy: XY,
        target_xys: Set[XY], real_target_xys: Set[XY],
        routes: Dict[XY, RoutingTree], overlaps: Set[XY]):
    """
    Route from multiple source connection points to all target chips.

    :param Machine machine: The machine to route on
    :param set(tuple(int,int)) source_edge_xys:
        Set of chips that routes are currently going outward from the source
        (updated here)
    :param tuple(int,int) target_edge_xy:
        The x and y coordinate of the actual target edge chip to route to
    :param list(tuple(int,int)) target_xys: The chips in the target
    :param set(tuple(int,int)) real_target_xys:
        The chips in the target that something in the source actually targets
    :param dict(tuple(int,int), RoutingTree) routes:
        The routes already made and to add to (updated here)
    :param set(tuple(int,int)) overlaps:
        Chips which overlap between source and target
    """
    # Deal with the overlaps first by finding the set of all things that can
    # be reached in the target from each of them, without hitting any other
    # overlaps, and routing the source from there directly
    reached_xys = set(overlaps)
    for overlap_xy in overlaps:
        targets = _find_reachable(overlap_xy, machine, target_xys, reached_xys)
        this_target_xys = {xy for xy in real_target_xys if xy in targets}
        _route_to_xys(
            overlap_xy, targets, machine, routes, this_target_xys,
            f"Overlap {overlap_xy} to Targets")

        # We now need to make sure the source edges go here too
        source_edge_xys.add(overlap_xy)

        # We also need to stop the targets we have found being needed in future
        for xy in this_target_xys:
            real_target_xys.remove(xy)
            target_xys.remove(xy)

        # And we need to stop next run of the loop going through chips
        # we have already done as more overlapping is not a good idea!
        reached_xys.update(targets)

    # Now do the last bit, which is getting to the rest of the chips
    _route_to_xys(
        target_edge_xy, target_xys, machine, routes,
        real_target_xys, "Target to Targets")


def _route_source_to_source(
        source: ApplicationVertex, partition: AbstractEdgePartition,
        targets: Dict[XY, _Targets], self_xys: Set[XY]):
    """
    Routes the source to itself.

    :param ApplicationVertex source: The source vertex to route
    :param AbstractEdgePartition partition: The partition being routed
    :param dict(tuple(int,int),_Targets) targets: Actual targets on the chips
    :param set(tuple(int,int)) self_xys:
        The coordinates of chips that are targets
    """
    # Add the targets of the sources
    target_vertices = source.splitter.get_source_specific_in_coming_vertices(
        source, partition.identifier)
    for tgt, srcs in target_vertices:
        xy, (_vertex, core, link) = vertex_xy_and_route(tgt)
        targets[xy].add_machine_sources_for_target(
            core, link, srcs, partition.identifier)
        self_xys.add(xy)


def _route_internal(
        internal_partitions: Iterable[MulticastEdgePartition],
        targets: Dict[XY, _Targets], self_xys: Set[XY]):
    """
    Route internal_partitions multicast edges.

    :param list(MulticastEdgePartition) internal_partitions:
        A list of partitions to route
    :param dict(tuple(int,int),_Targets) targets: Actual things to target
    :param set(tuple(int,int)) self_xys: Chips to target
    """
    for in_part in internal_partitions:
        src = in_part.pre_vertex
        for edge in in_part.edges:
            tgt = edge.post_vertex
            xy, (_vertex, core, link) = vertex_xy_and_route(tgt)
            targets[xy].add_machine_sources_for_target(
                core, link, [src], in_part.identifier)
            self_xys.add(xy)


def _make_source_to_target_routes(
        source: ApplicationVertex, partition: AbstractEdgePartition,
        source_edge_xys: Set[XY],
        source_mappings: Dict[XY, List[_MappedSrc]],
        targets: Dict[XY, _Targets],
        routing_tables: MulticastRoutingTableByPartition,
        routes: Dict[XY, RoutingTree]):
    """
    Convert the routes from source to targets into routing table entries.

    :param ApplicationVertex source: The source application vertex
    :param AbstractEdgePartition partition: The partition to route
    :param set(tuple(int,int)) source_edge_xys:
        Set of chips that routes are currently going outward from the source
    :param source_mappings: The sources mapped to their routes
    :type source_mappings: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
        tuple(MachineVertex, None, int)))
    :param dict(tuple(int,int),_Targets) targets:
        The actual targets to hit on each chip
    :param MulticastRoutingTableByPartition routing_tables: The tables to write
    :param dict(tuple(int,int),RoutingTree) routes: The routes to convert
    """
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


def _make_source_to_source_routes(
        all_source_xys: Set[XY], source_edge_xys: Set[XY],
        self_xys: Set[XY],
        source_mappings: Dict[XY, List[_MappedSrc]],
        machine: Machine, partition: AbstractEdgePartition,
        routing_tables: MulticastRoutingTableByPartition,
        targets: Dict[XY, _Targets]):
    """
    Convert the routes from the source vertices themselves when the source
    is self-connected.

    :param list(tuple(int,int)) all_source_xys: All source chips
    :param set(tuple(int,int)) source_edge_xys:
        Set of chips that routes are going outward from the source
    :param self_xys: The actual chips that are targeted in the source
    :param source_mappings: The sources mapped to their routes
    :type source_mappings: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
        tuple(MachineVertex, None, int)))
    :param Machine machine: The machine to route on
    :param AbstractEdgePartition partition: The partition to route
    :param MulticastRoutingTableByPartition routing_tables: The tables to write
    :param dict(tuple(int,int),_Targets) targets:
        The target end-points of the routes
    """
    for xy in source_mappings:
        source_routes: Dict[XY, RoutingTree] = dict()
        _route_to_xys(
            xy, all_source_xys, machine, source_routes,
            source_edge_xys.union(self_xys),
            "Sources to Source (self)")
        for vertex, processor, link in source_mappings[xy]:
            _convert_a_route(
                routing_tables, vertex, partition.identifier,
                processor, link, source_routes[xy], targets=targets,
                use_source_for_targets=True)


def _make_source_to_source_edge_routes(
        all_source_xys: Set[XY], source_edge_xys: Iterable[XY],
        source_mappings: Dict[XY, List[_MappedSrc]],
        machine: Machine, partition: AbstractEdgePartition,
        routing_tables: MulticastRoutingTableByPartition):
    """
    Convert the routes from the source vertices to the edge vertices when
    the source is not self-connected.

    :param list(tuple(int,int)) all_source_xys: All source chips
    :param set(tuple(int,int)) source_edge_xys:
        Set of chips that routes are going outward from the source
    :param source_mappings: The sources mapped to their routes
    :type source_mappings: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
        tuple(MachineVertex, None, int)))
    :param Machine machine: The machine to route on
    :param AbstractEdgePartition partition: The partition to route
    :param MulticastRoutingTableByPartition routing_tables: The tables to write
    """
    for xy in source_mappings:
        source_routes: Dict[XY, RoutingTree] = dict()
        _route_to_xys(
            xy, all_source_xys, machine, source_routes,
            source_edge_xys, "Sources to source")
        for vertex, processor, link in source_mappings[xy]:
            _convert_a_route(
                routing_tables, vertex, partition.identifier,
                processor, link, source_routes[xy], dict())


def _find_target_xy(
        target_xys: Set[XY], routes: Dict[XY, RoutingTree],
        source_mappings: Dict[XY, List[_MappedSrc]]) -> Tuple[
            XY, Optional[Set[XY]]]:
    """
    Find a target chip to use from the set of target chips.

    :param set(tuple(int, int)) target_xys:
        The chips in the target; must not be empty
    :param dict(tuple(int,int),RoutingTree) routes: The routes in existence
    :param source_mappings: The sources mapped to their routes
    :type source_mappings: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
        tuple(MachineVertex, None, int)))
    :return: A chip to use as a target, and the set of overlapping chips
    :rtype: tuple(tuple(int, int), set(tuple(x, y)) or None)
    """
    overlaps = target_xys.intersection(source_mappings)

    if overlaps:
        target_chip = next(iter(overlaps))
        # Multiple overlaps is a special case (and very unusual, normally only
        # when there is an FPGA device with multiple incoming chips)
        if len(overlaps) > 1:
            return target_chip, overlaps

        # If only one overlap, we can leave that to normal case, so say none
        return target_chip, None

    for xy in target_xys:
        if xy in routes:
            return xy, None
    return xy, None  # pylint:disable=undefined-loop-variable


def _get_outgoing_mapping(
        app_vertex: ApplicationVertex, partition_id: str) -> Dict[
            XY, List[_MappedSrc]]:
    """
    Gets a Mapping from x,y sources to a list of (vertex, the vertex,
    processor and link to follow to get to the vertex.

    For each tuple in the list either processor or link will be `None`.

    :param ApplicationVertex app_vertex:
    :param str partition_id:
    :rtype: dict(tuple(int, int),
        list(tuple(MachineVertex, int,  None) or
             tuple(MachineVertex, None, int)))
    """
    outgoing_mapping: Dict[XY, List[_MappedSrc]] = defaultdict(list)
    for m_vertex in app_vertex.splitter.get_out_going_vertices(partition_id):
        xy, route = vertex_xy_and_route(m_vertex)
        outgoing_mapping[xy].append(route)
    for in_part in app_vertex.splitter.get_internal_multicast_partitions():
        if in_part.identifier == partition_id:
            xy, route = vertex_xy_and_route(in_part.pre_vertex)
            outgoing_mapping[xy].append(route)
    return outgoing_mapping


def _get_all_xys(app_vertex: ApplicationVertex) -> Set[XY]:
    """
    Gets the list of all the x,y coordinates that the vertex's machine vertices
    are placed on.

    :param ApplicationVertex app_vertex:
    :rtype: set(tuple(int, int))
    """
    return {vertex_xy(m_vertex)
            for m_vertex in app_vertex.machine_vertices}


def _route_to_xys(
        first_xy: XY, all_xys: Set[XY], machine: Machine,
        routes: Dict[XY, RoutingTree], targets: Iterable[XY], label: str):
    """
    :param tuple(int, int) first_xy:
    :param list(tuple(int, int)) all_xys:
    :param ~spinn_machine.Machine machine:
    :param routes:
    :param targets:
    :param str label:
    """
    # Keep a queue of xy to visit, list of (parent xy, link from parent)
    xys_to_explore: Deque[Tuple[XY, List[Tuple[XY, int]]]] = deque(
        [(first_xy, list())])
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
        raise PacmanRoutingException(
            f"Failed to visit all targets {targets} from {first_xy}: "
            f"Not visited {targets_to_visit}")


def _find_reachable(
        source_xy: XY, machine: Machine, allowed_xys: Set[XY],
        disallowed_xys: Set[XY]) -> Set[XY]:
    """
    Find a set of chips that can be reached from a source only via the
    allowed chips, but not looking at the disallowed chips.  A chip in
    the disallowed chips is not used unless it is the source even if in the
    allowed chips!

    :param tuple(int,int) source_xy:
    :param Machine machine:
    :param set(tuple(int,int)) allowed_xys:
    :param set(tuple(int,int)) disallowed_xys:
    :rtype: set(tuple(int,int))
    """
    xys_to_explore = deque([source_xy])
    visited = set()
    while xys_to_explore:
        xy = xys_to_explore.pop()
        if xy in visited:
            continue
        visited.add(xy)
        for link in range(6):
            x, y = xy
            if machine.is_link_at(x, y, link):
                next_xy = machine.xy_over_link(x, y, link)
                if (_is_open_chip(next_xy, allowed_xys, visited, machine) and
                        next_xy not in disallowed_xys):
                    xys_to_explore.append(next_xy)
    return visited


def _is_open_chip(
        xy: XY, xy_set: Set[XY], visited: Set[XY],
        machine: Machine) -> bool:
    """
    :param tuple(int, int) xy: Coordinates
    :param set(tuple(int, int) xy_set: List of legal coordinates
    :param set(tuple(int, int) visited:
    :param ~spinn_machine.Machine machine:
    :return: True if the coordinates point to an existing Chip not yet visited
    :rtype: bool
    """
    return xy in xy_set and xy not in visited and machine.is_chip_at(*xy)


def _route_pre_to_post(
        source_xy: XY, dest_xy: XY, routes: Dict[XY, RoutingTree],
        machine: Machine, label: str, all_source_xy: Set[XY],
        target_xys: Set[XY]) -> Tuple[XY, XY]:
    """
    :param tuple(int, int) source_xy:
    :param tuple(int, int) dest_xy:
    :param dict(tuple(int,int), RoutingTree) routes:
    :param ~spinn_machine.Machine machine:
    :param str label:
    :param set(tuple(int, int)) all_source_xy:
    :param set(tuple(int, int)) target_xys:
    :return: the pre- and post-vertex coordinates
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
    for i, (_direction, xy) in reversed(list(enumerate(nodes))):
        if xy in all_source_xy or xy in routes:
            nodes = nodes[i + 1:]
            route_pre = xy
            break

    # If we found one not in the route, create a new entry for it
    if route_pre not in routes:
        routes[route_pre] = RoutingTree(route_pre, label)

    # Start from the start and move forwards until we find a chip in
    # the target group
    route_post = dest_xy
    for i, (_direction, xy) in enumerate(nodes):
        if xy in target_xys:
            nodes = nodes[:i + 1]
            route_post = xy
            break

    # Convert nodes to routes and add to existing routes
    source_route = routes[route_pre]
    for direction, dest_node in nodes:
        if dest_node in routes:
            _print_path(routes[source_xy])
            print(f"Direct path from {source_xy} to {dest_xy}: {nodes_direct}")
            print(f"Avoiding down chips: {nodes_fixed}")
            print(f"Trimmed path is from {route_pre} to {route_post}: {nodes}")
            raise PacmanRoutingException(
                f"Somehow node {dest_node} already in routes with label"
                f" {routes[dest_node].label}")
        dest_route = RoutingTree(dest_node, label)
        routes[dest_node] = dest_route
        source_route.append_child((direction, dest_route))
        source_route = dest_route

    return route_pre, route_post


def _path_without_errors(
        source_xy: XY, nodes: List[_Node],
        machine: Machine) -> List[_Node]:
    """
    :param tuple(int, int) source_xy:
    :param  list(tuple(int,tuple(int, int))) nodes:
    :param ~spinn_machine.Machine machine:
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


def _path_without_loops(start_xy: XY, nodes: List[_Node]) -> List[_Node]:
    """
    :param tuple(int, int) start_xy:
    :param list(tuple(int,tuple(int,int))) nodes:
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


def _is_ok(xy: XY, node: _Node, machine: Machine):
    """
    :param tuple(int, int) xy:
    :param tuple(int,tuple(int, int)) node:
    :param ~spinn_machine.Machine machine:
    :rtype: bool
    """
    c_x, c_y = xy
    direction, (n_x, n_y) = node
    return machine.is_link_at(c_x, c_y, direction) \
        and machine.is_chip_at(n_x, n_y)


def _xy(node: _Node) -> XY:
    _, xy = node
    return xy


def _find_path(
        source_xy: XY, target_xy: XY, machine: Machine) -> List[_Node]:
    """
    :param tuple(int,int) source_xy:
    :param tuple(int,int) target_xy:
    :param Machine machine:
    :rtype: list(tuple(int,tuple(int,int)))
    """
    xys_to_explore: Deque[Tuple[XY, List[_Node]]] = deque(
        [(source_xy, list())])
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
                next_xy: XY = machine.xy_over_link(x, y, link)
                if _is_open_chip(next_xy, set((next_xy,)), visited, machine):
                    new_path = list(path)
                    new_path.append((link, next_xy))
                    xys_to_explore.append((next_xy, new_path))
    raise PacmanRoutingException(f"No path from {source_xy} to {target_xy}")


def _convert_a_route(
        routing_tables: MulticastRoutingTableByPartition,
        source_vertex: _AnyVertex, partition_id: str,
        first_incoming_processor: _OptInt, first_incoming_link: _OptInt,
        first_route: RoutingTree, targets: Dict[XY, _Targets],
        use_source_for_targets: bool = False,
        ensure_all_source: bool = False):
    """
    Convert the algorithm specific partition_route back to SpiNNaker and
    adds it to the routing_tables.

    :param MulticastRoutingTableByPartition routing_tables:
        spinnaker format routing tables
    :param source_vertex: The source to be added to the table
    :type source_vertex: ApplicationVertex or MachineVertex
    :param incoming_processor: processor this link came from
    :type incoming_processor: int or None
    :param incoming_link: link this link came from
    :type incoming_link: int or None
    :param targets:
        Targets for each chip.  When present for a chip, the route links and
        cores are added to each entry in the targets.
    :type targets: dict(tuple(int,int),_Targets) or None
    :param bool use_source_for_targets:
        If true, targets for the given source_vertex will be requested;
        If false all targets for matching chips will be used.
    :param bool ensure_all_source:
        If true, ensures that all machine vertices of the source application
        vertex are covered in routes that continue forward
    """
    to_process: List[Tuple[_OptInt, _OptInt, RoutingTree]] = [
        (first_incoming_processor, first_incoming_link, first_route)]
    while to_process:
        incoming_processor, incoming_link, route = to_process.pop()
        x, y = route.chip

        processor_ids: List[int] = list()
        link_ids: List[int] = list()
        for (link, next_hop) in route.children:
            if link is not None:
                link_ids.append(link)
                next_incoming_link = (link + 3) % 6
            if next_hop is not None:
                assert isinstance(next_hop, RoutingTree)
                to_process.append((None, next_incoming_link, next_hop))

        if (x, y) in targets:
            chip_targets = targets[x, y]
            targets_by_source: Iterable[
                Tuple[_AnyVertex, Tuple[List[int], List[int]]]]
            if use_source_for_targets:
                targets_by_source = [
                    chip_targets.get_targets_for_source(source_vertex)]
            else:
                targets_by_source = chip_targets.targets_by_source

            # We must ensure that all machine vertices of an app vertex
            # are covered!
            machine_vertex_sources: Set[MachineVertex] = set()
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
                assert isinstance(source_vertex, ApplicationVertex)
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
        first_route: RoutingTree,
        routing_tables: MulticastRoutingTableByPartition,
        entry: MulticastRoutingTableByPartitionEntry,
        x: int, y: int, source: _AnyVertex, partition_id: str):
    try:
        routing_tables.add_path_entry(entry, x, y, source, partition_id)
    except Exception as e:
        print(f"Error adding route: {e}")
        _print_path(first_route)
        raise e


def _print_path(first_route: RoutingTree):
    to_process: List[Tuple[str, _OptInt, RoutingTree]] = [
        ("", None, first_route)]
    last_is_leaf = False
    line = ""
    visited = set()
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

        if route.chip in visited:
            print(line, "Loop!")
            line = ""
            last_is_leaf = True
        elif route.is_leaf:
            # This is a leaf
            last_is_leaf = True
            print(line)
            line = ""
        else:
            last_is_leaf = False
            for direction, next_route in route.children:
                assert isinstance(next_route, RoutingTree)
                to_process.append((prefix, direction, next_route))

        visited.add(route.chip)
