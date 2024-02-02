# Copyright (c) 2014 The University of Manchester
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

import logging
import sys
from collections import defaultdict
from typing import Dict, Tuple, Set, Optional, List, Iterable
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from spinn_machine import Chip, Link
from pacman.data import PacmanDataView
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    get_app_partitions, vertex_xy_and_route)
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationEdgePartition)
from pacman.model.graphs.machine import MachineVertex
_OptInt = Optional[int]

logger = FormatAdapter(logging.getLogger(__name__))
infinity = float("inf")

#: Assumed bandwidth cost per entry.
BW_PER_ROUTE_ENTRY = 0.01
#: Maximum bandwidth of a link.
MAX_BW = 250
# pylint: disable=wrong-spelling-in-comment


class _NodeInfo(object):
    """
    :ivar list(~spinn_machine.Link) neighbours:
    :ivar list(float) weights:
    """
    __slots__ = ("neighbours", "weights")

    def __init__(self) -> None:
        self.neighbours: List[Optional[Link]] = list()
        self.weights: List[float] = list()

    @property
    def neighweights(self) -> Iterable[Tuple[Optional[Link], float]]:
        """
        Zip of neighbours and their weights

        :rtype: iterable(link or None, float)
        """
        return zip(self.neighbours, self.weights)


class _DijkstraInfo(object):
    __slots__ = ("activated", "cost")

    def __init__(self) -> None:
        self.activated = False
        self.cost: Optional[float] = None


class _DestInfo:
    __slots__ = ("cores", "links")

    def __init__(self) -> None:
        self.cores: Set[int] = set()
        self.links: Set[int] = set()


def basic_dijkstra_routing():
    """
    Find routes between the edges with the allocated information,
    placed in the given places

    :return: The discovered routes
    :rtype: MulticastRoutingTables
    :raise PacmanRoutingException:
        If something goes wrong with the routing
    """
    router = _BasicDijkstraRouting()
    return router.route_all_partitions()


class _BasicDijkstraRouting(object):
    """
    A routing algorithm that can find routes for edges between vertices
    in a machine graph that have been placed on a machine by the use of a
    Dijkstra shortest path algorithm.
    """

    __slots__ = (
        # the routing path objects used to be returned to the work flow
        "_routing_paths", )

    def __init__(self) -> None:
        # set up basic data structures
        self._routing_paths = MulticastRoutingTableByPartition()

    def route_all_partitions(self) -> MulticastRoutingTableByPartition:
        """
        Find routes between the edges with the allocated information,
        placed in the given places

        :param bool use_progress_bar: whether to show a progress bar
        :return: The discovered routes
        :rtype: MulticastRoutingTableByPartition
        :raise PacmanRoutingException:
            If something goes wrong with the routing
        """

        nodes_info = self._initiate_node_info()
        tables = self._initiate_dijkstra_tables()
        self._update_all_weights(nodes_info)

        partitions = get_app_partitions()
        progress = ProgressBar(len(partitions), "Creating routing entries")

        for partition in progress.over(partitions):
            self._route(partition, nodes_info, tables)
        return self._routing_paths

    @staticmethod
    def __vertex_and_route(tgt) -> Tuple[
            Chip, Tuple[MachineVertex, _OptInt, _OptInt]]:
        xy, details = vertex_xy_and_route(tgt)
        return PacmanDataView.get_chip_at(*xy), details

    def _route(self, partition: ApplicationEdgePartition,
               node_info: Dict[Chip, _NodeInfo],
               tables: Dict[Chip, _DijkstraInfo]):
        """
        :param ApplicationEdgePartition partition:
        :param dict(Chip,_NodeInfo) node_info:
        :param dict(Chip,_DijkstraInfo) tables:
        """
        # pylint: disable=too-many-arguments
        source = partition.pre_vertex

        # Destination (dst, core, link) by source machine vertices
        destinations: Dict[MachineVertex, Dict[Chip, _DestInfo]] = \
            defaultdict(lambda: defaultdict(_DestInfo))
        dest_chips: Dict[MachineVertex, Set[Chip]] = defaultdict(set)

        for edge in partition.edges:
            target = edge.post_vertex
            target_vertices = \
                target.splitter.get_source_specific_in_coming_vertices(
                    source, partition.identifier)

            for tgt, srcs in target_vertices:
                dst, (m_vertex, core, link) = self.__vertex_and_route(tgt)
                for src in srcs:
                    if isinstance(src, ApplicationVertex):
                        for s in src.splitter.get_out_going_vertices(
                                partition.identifier):
                            if core is not None:
                                destinations[s][dst].cores.add(core)
                            if link is not None:
                                destinations[s][dst].links.add(link)
                            dest_chips[s].add(dst)
                    else:
                        if core is not None:
                            destinations[src][dst].cores.add(core)
                        if link is not None:
                            destinations[src][dst].links.add(link)
                        dest_chips[src].add(dst)

        outgoing: OrderedSet[MachineVertex] = OrderedSet(
            source.splitter.get_out_going_vertices(partition.identifier))
        for in_part in source.splitter.get_internal_multicast_partitions():
            if in_part.identifier == partition.identifier:
                outgoing.add(in_part.pre_vertex)
                for edge in in_part.edges:
                    dst, (_tgt, core, link) = self.__vertex_and_route(
                        edge.post_vertex)
                    if core is not None:
                        destinations[in_part.pre_vertex][dst].cores.add(core)
                    if link is not None:
                        destinations[in_part.pre_vertex][dst].links.add(link)
                    dest_chips[in_part.pre_vertex].add(dst)

        for m_vertex in outgoing:
            src, (m_vertex, core, link) = self.__vertex_and_route(m_vertex)
            if dest_chips[m_vertex]:
                self._update_all_weights(node_info)
                self._reset_tables(tables)
                tables[src].activated = True
                tables[src].cost = 0
                self._propagate_costs_until_reached_destinations(
                    tables, node_info, dest_chips[m_vertex], src)

            for dst, info in destinations[m_vertex].items():
                self._retrace_back_to_source(
                    dst, info, tables, node_info, core,
                    link, m_vertex, partition.identifier)

    def _initiate_node_info(self) -> Dict[Chip, _NodeInfo]:
        """
        Set up a dictionary which contains data for each chip in the
        machine.

        :return: nodes_info dictionary
        :rtype: dict(Chip,_NodeInfo)
        """
        nodes_info = dict()
        for chip in PacmanDataView.get_machine().chips:
            # get_neighbours should return a list of
            # dictionaries of 'x' and 'y' values
            node = _NodeInfo()
            for source_id in range(6):
                node.neighbours.append(chip.router.get_link(source_id))
                node.weights.append(infinity)
            nodes_info[chip] = node
        return nodes_info

    def _initiate_dijkstra_tables(self) -> Dict[Chip, _DijkstraInfo]:
        """
        Set up the Dijkstra's table which includes if you've reached a
        given node.

        :return: the  Dijkstra's table dictionary
        :rtype: dict(Chip,_DijkstraInfo)
        """
        # Holds all the information about nodes within one full run of
        # Dijkstra's algorithm
        return {
            chip: _DijkstraInfo()
            for chip in PacmanDataView.get_machine().chips}

    def _update_all_weights(self, nodes_info: Dict[Chip, _NodeInfo]):
        """
        Change the weights of the neighbouring nodes.

        :param dict(Chip,_NodeInfo) nodes_info:
            the node info dictionary
        """
        for key in nodes_info:
            if nodes_info[key] is not None:
                self._update_neighbour_weights(nodes_info, key)

    def _update_neighbour_weights(
            self, nodes_info: Dict[Chip, _NodeInfo], key: Chip):
        """
        Change the weights of the neighbouring nodes.

        :param dict(Chip,_NodeInfo) nodes_info:
            the node info dictionary
        :param Chip key:
            the identifier to the object in `nodes_info`
        """
        for n, neighbour in enumerate(nodes_info[key].neighbours):
            if neighbour is not None:
                nodes_info[key].weights[n] = 1

    @staticmethod
    def _reset_tables(tables: Dict[Chip, _DijkstraInfo]):
        """
        Reset the Dijkstra tables for a new path search.

        :param dict(Chip,_DijkstraInfo) tables:
            the dictionary object for the Dijkstra-tables
        """
        for key in tables:
            tables[key] = _DijkstraInfo()

    def _propagate_costs_until_reached_destinations(
            self, tables: Dict[Chip, _DijkstraInfo],
            nodes_info: Dict[Chip, _NodeInfo], dest_chips: Set[Chip],
            source: Chip):
        """
        Propagate the weights till the destination nodes of the source
        nodes are retraced.

        :param dict(Chip,_DijkstraInfo) tables:
            the dictionary object for the Dijkstra-tables
        :param dict(Chip,_NodeInfo) nodes_info:
            the dictionary object for the nodes inside a route scope
        :param set(Chip) dest_chips:
        :param Chip source:
        :raise PacmanRoutingException:
            when the destination node could not be reached from this source
            node
        """
        dest_chips_to_find = set(dest_chips)
        dest_chips_to_find.discard(source)

        current = source

        # Iterate only if the destination node hasn't been activated
        while dest_chips_to_find:
            # PROPAGATE!
            for neighbour, weight in nodes_info[current].neighweights:
                # "neighbours" is a list of 6 links or None objects. There is
                # a None object where there is no connection to that neighbour
                if neighbour is not None and not (
                        neighbour.destination_x == source.x and
                        neighbour.destination_y == source.y):
                    # These variables change with every look at a new neighbour
                    self._update_neighbour(
                        tables, neighbour, current, source, weight)

            # Set the next activated node as the deactivated node with the
            # lowest current cost
            current = self._minimum(tables)
            tables[current].activated = True
            dest_chips_to_find.discard(current)

    @staticmethod
    def _minimum(tables: Dict[Chip, _DijkstraInfo]) -> Chip:
        """
        :param dict(Chip,_DijkstraInfo) tables:
        :rtype: tuple(int,int)
        """
        # This is the lowest cost across ALL deactivated nodes in the graph.
        lowest_cost: float = sys.maxsize
        lowest: Optional[Chip] = None

        # Find the next node to be activated
        for key in tables:
            cost = tables[key].cost
            # Don't continue if the node hasn't even been touched yet
            if (cost is not None and not tables[key].activated
                    and cost < lowest_cost):
                lowest_cost, lowest = cost, key

        # If there were no deactivated nodes with costs, but the destination
        # was not reached this iteration, raise an exception
        if lowest is None:
            raise PacmanRoutingException(
                "Destination could not be activated, ending run")

        return lowest

    @staticmethod
    def __get_neighbour_destination(neighbour: Link) -> Optional[Chip]:
        return PacmanDataView.get_machine().get_chip_at(
            neighbour.destination_x, neighbour.destination_y)

    def _update_neighbour(
            self, tables: Dict[Chip, _DijkstraInfo], neighbour: Link,
            current: Chip, source: Chip, weight: float):
        """
        Update the lowest cost for each neighbouring chip of a node.

        :param dict(Chip,_DijkstraInfo) tables:
        :param ~spinn_machine.Link neighbour:
        :param Chip current:
        :param Chip source:
        :param float weight:
        :raise PacmanRoutingException: when the algorithm goes to a node that
            doesn't exist in the machine or the node's cost was set too low.
        """
        neighbour_chip = self.__get_neighbour_destination(neighbour)
        if not neighbour_chip or neighbour_chip not in tables:
            raise PacmanRoutingException(
                f"Tried to propagate to ({neighbour.destination_x}, "
                f"{neighbour.destination_y}), which is not in the"
                " graph: remove non-existent neighbours")

        chip_cost = tables[current].cost
        assert chip_cost is not None
        neighbour_cost = tables[neighbour_chip].cost

        # Only try to update if the neighbour_chip is within the graph and the
        # cost if the node hasn't already been activated and the lowest cost
        # if the new cost is less, or if there is no current cost.
        new_weight = float(chip_cost + weight)
        if not tables[neighbour_chip].activated and (
                neighbour_cost is None or new_weight < neighbour_cost):
            # update Dijkstra table
            tables[neighbour_chip].cost = new_weight

        if tables[neighbour_chip].cost == 0 and neighbour_chip != source:
            raise PacmanRoutingException(
                f"!!!Cost of non-source node ({neighbour.destination_x}, "
                f"{neighbour.destination_y}) was set to zero!!!")

    def _retrace_back_to_source(
            self, dest: Chip, dest_info: _DestInfo,
            tables: Dict[Chip, _DijkstraInfo],
            nodes_info: Dict[Chip, _NodeInfo],
            source_processor: _OptInt, source_link: _OptInt,
            pre_vertex, partition_id) -> None:
        """
        :param Placement dest: Destination placement
        :param _DestInfo dest_info: Information for building an entry
        :param dict(Chip,_DijkstraInfo) tables:
        :param MachineEdge edge:
        :param dict(Chip,_NodeInfo) nodes_info:
        :param int source_processor:
        :param int source_link:
        :raise PacmanRoutingException:
            when the algorithm doesn't find a next point to search from. AKA,
            the neighbours of a chip do not have a cheaper cost than the node
            itself, but the node is not the destination or when the algorithm
            goes to a node that's not considered in the weighted search.
        """
        entry = MulticastRoutingTableByPartitionEntry(
            dest_info.links, dest_info.cores)
        self._routing_paths.add_path_entry(
            entry, dest.x, dest.y, pre_vertex, partition_id)
        prev_entry = entry

        while tables[dest].cost != 0:
            for idx, neighbour in enumerate(nodes_info[dest].neighbours):
                if neighbour is not None:
                    n = self.__get_neighbour_destination(neighbour)

                    # Only check if it can be a preceding node if it actually
                    # exists
                    if not n or n not in tables:
                        raise PacmanRoutingException(
                            "Tried to trace back to node not in "
                            "graph: remove non-existent neighbours")

                    if tables[n].cost is not None:
                        dest, prev_entry, added = self._create_routing_entry(
                            n, tables, idx, nodes_info, dest,
                            prev_entry, pre_vertex, partition_id)
                        if added:
                            break
            else:
                raise PacmanRoutingException(
                    "Iterated through all neighbours of tracking node but"
                    " did not find a preceding node! Consider increasing "
                    "acceptable discrepancy between sought traceback cost"
                    " and actual cost at node. Terminating...")
        if source_processor is not None:
            prev_entry.incoming_processor = source_processor
        if source_link is not None:
            prev_entry.incoming_link = source_link

    def _create_routing_entry(
            self, neighbour: Chip, tables: Dict[Chip, _DijkstraInfo],
            neighbour_index: int, nodes_info: Dict[Chip, _NodeInfo],
            dest: Chip, previous_entry: MulticastRoutingTableByPartitionEntry,
            pre_vertex, partition_id) -> Tuple[
                Chip, MulticastRoutingTableByPartitionEntry, bool]:
        """
        Create a new routing entry.

        :param Chip neighbour:
        :param dict(Chip,_DijkstraInfo) tables:
        :param int neighbour_index:
        :param dict(Chip,_NodeInfo) nodes_info:
        :param Chip dest:
        :param MulticastRoutingTableByPartitionEntry previous_entry:
        :return: dest, previous_entry, made_an_entry
        :rtype: tuple(Chip, MulticastRoutingTableByPartitionEntry, bool)
        :raise PacmanRoutingException:
            when the bandwidth of a router is beyond expected parameters
        """
        # Set the direction of the routing other_entry as that which is from
        # the preceding node to the current tracking node.
        # neighbour is the 'old' chip since it is from the preceding node.
        # dest is the 'new' chip since it is where the router should send the
        # packet to.
        dec_direction = (3, 4, 5, 0, 1, 2)[neighbour_index]
        made_an_entry = False

        neighbour_weight = nodes_info[neighbour].weights[dec_direction]
        chip_sought_cost = tables[dest].cost
        assert chip_sought_cost is not None
        chip_sought_cost -= neighbour_weight
        neighbours_lowest_cost = tables[neighbour].cost

        if neighbours_lowest_cost is not None and (
                self._close_enough(neighbours_lowest_cost, chip_sought_cost)):
            # build the multicast entry
            entry = MulticastRoutingTableByPartitionEntry(dec_direction, None)
            previous_entry.incoming_link = neighbour_index
            # add entry for next hop going backwards into path
            self._routing_paths.add_path_entry(
                entry, neighbour.x, neighbour.y, pre_vertex, partition_id)
            previous_entry = entry
            made_an_entry = True

            # Finally move the tracking node
            dest = neighbour

        return dest, previous_entry, made_an_entry

    @staticmethod
    def _close_enough(v1: float, v2: float, delta=0.00000000001) -> bool:
        """
        :param float v1:
        :param float v2:
        :param float delta: How close values have to be to be "equal"
        """
        return abs(v1 - v2) < delta
