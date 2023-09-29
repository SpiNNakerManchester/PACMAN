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
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from pacman.data import PacmanDataView
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)
from pacman.utilities.algorithm_utilities.routing_algorithm_utilities import (
    get_app_partitions, vertex_xy_and_route)
from pacman.model.graphs.application import ApplicationVertex

logger = FormatAdapter(logging.getLogger(__name__))
infinity = float("inf")

BW_PER_ROUTE_ENTRY = 0.01
MAX_BW = 250


class _NodeInfo(object):
    """
    :ivar list(~spinn_machine.Link) neighbours:
    :ivar list(float) bws:
    :ivar list(float) weights:
    """
    __slots__ = ["neighbours", "bws", "weights"]

    def __init__(self):
        self.neighbours = list()
        self.bws = list()
        self.weights = list()

    @property
    def neighweights(self):
        return zip(self.neighbours, self.weights)


class _DijkstraInfo(object):
    __slots__ = ["activated", "cost"]

    def __init__(self):
        self.activated = False
        self.cost = None


def basic_dijkstra_routing(
        bw_per_route_entry=BW_PER_ROUTE_ENTRY, max_bw=MAX_BW):
    """
    Find routes between the edges with the allocated information,
    placed in the given places

    :param bool use_progress_bar: whether to show a progress bar
    :return: The discovered routes
    :rtype: MulticastRoutingTables
    :raise PacmanRoutingException:
        If something goes wrong with the routing
    """
    router = _BasicDijkstraRouting(bw_per_route_entry, max_bw)
    # pylint:disable=protected-access
    return router._run()


class _BasicDijkstraRouting(object):
    """
    A routing algorithm that can find routes for edges between vertices
    in a machine graph that have been placed on a machine by the use of a
    Dijkstra shortest path algorithm.
    """

    __slots__ = [
        # the routing path objects used to be returned to the work flow
        "_routing_paths",

        # parameter to control ...........
        "_bw_per_route_entry",

        # parameter to control ...........
        "_max_bw"
    ]

    def __init__(self, bw_per_route_entry, max_bw):
        # set up basic data structures
        self._routing_paths = MulticastRoutingTableByPartition()
        self._bw_per_route_entry = bw_per_route_entry
        self._max_bw = max_bw

    def _run(self):
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

    def _route(self, partition, node_info, tables):
        """
        :param ApplicationEdgePartition partition:
        :param ApplicationGraph graph:
        :param dict(tuple(int,int),_NodeInfo) node_info:
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :param Machine machine:
        """
        # pylint: disable=too-many-arguments
        source = partition.pre_vertex

        # Destination (xy, core, link) by source machine vertices
        destinations = defaultdict(lambda: defaultdict(lambda: (set(), set())))
        dest_chips = defaultdict(set)

        for edge in partition.edges:
            target = edge.post_vertex
            target_vertices = \
                target.splitter.get_source_specific_in_coming_vertices(
                    source, partition.identifier)

            for tgt, srcs in target_vertices:
                xy, (m_vertex, core, link) = vertex_xy_and_route(tgt)
                for src in srcs:
                    if isinstance(src, ApplicationVertex):
                        for s in src.splitter.get_out_going_vertices(
                                partition.identifier):
                            if core is not None:
                                destinations[s][xy][0].add(core)
                            if link is not None:
                                destinations[s][xy][1].add(link)
                            dest_chips[s].add(xy)
                    else:
                        if core is not None:
                            destinations[src][xy][0].add(core)
                        if link is not None:
                            destinations[src][xy][1].add(link)
                        dest_chips[src].add(xy)

        outgoing = OrderedSet(source.splitter.get_out_going_vertices(
            partition.identifier))
        for in_part in source.splitter.get_internal_multicast_partitions():
            if in_part.identifier == partition.identifier:
                outgoing.add(in_part.pre_vertex)
                for edge in in_part.edges:
                    xy, (_tgt, core, link) = vertex_xy_and_route(
                        edge.post_vertex)
                    if core is not None:
                        destinations[in_part.pre_vertex][xy][0].add(core)
                    if link is not None:
                        destinations[in_part.pre_vertex][xy][1].add(link)
                    dest_chips[in_part.pre_vertex].add(xy)

        for m_vertex in outgoing:
            source_xy, (m_vertex, core, link) = vertex_xy_and_route(m_vertex)
            if dest_chips[m_vertex]:
                self._update_all_weights(node_info)
                self._reset_tables(tables)
                tables[source_xy].activated = True
                tables[source_xy].cost = 0
                x, y = source_xy
                self._propagate_costs_until_reached_destinations(
                    tables, node_info, dest_chips[m_vertex], x, y)

            for xy in destinations[m_vertex]:
                dest_cores, dest_links = destinations[m_vertex][xy]
                self._retrace_back_to_source(
                    xy, dest_cores, dest_links, tables, node_info, core, link,
                    m_vertex, partition.identifier)

    def _initiate_node_info(self):
        """
        Set up a dictionary which contains data for each chip in the
        machine.

        :return: nodes_info dictionary
        :rtype: dict(tuple(int,int),_NodeInfo)
        """
        nodes_info = dict()
        for chip in PacmanDataView.get_machine().chips:
            # get_neighbours should return a list of
            # dictionaries of 'x' and 'y' values
            node = _NodeInfo()
            for source_id in range(6):
                n = chip.router.get_link(source_id)
                node.neighbours.append(n)
                node.weights.append(infinity)
                node.bws.append(None if n is None else self._max_bw)
            nodes_info[chip.x, chip.y] = node
        return nodes_info

    def _initiate_dijkstra_tables(self):
        """
        Set up the Dijkstra's table which includes if you've reached a
        given node.

        :return: the  Dijkstra's table dictionary
        :rtype: dict(tuple(int,int),_DijkstraInfo)
        """
        # Holds all the information about nodes within one full run of
        # Dijkstra's algorithm
        tables = dict()
        for chip in PacmanDataView.get_machine().chips:
            tables[chip.x, chip.y] = _DijkstraInfo()
        return tables

    def _update_all_weights(self, nodes_info):
        """
        Change the weights of the neighbouring nodes.

        :param dict(tuple(int,int),_NodeInfo) nodes_info:
            the node info dictionary
        """
        for key in nodes_info:
            if nodes_info[key] is not None:
                self._update_neighbour_weights(nodes_info, key)

    def _update_neighbour_weights(self, nodes_info, key):
        """
        Change the weights of the neighbouring nodes.

        :param dict(tuple(int,int),_NodeInfo) nodes_info:
            the node info dictionary
        :param tuple(int,int) key:
            the identifier to the object in `nodes_info`
        """
        for n, neighbour in enumerate(nodes_info[key].neighbours):
            if neighbour is not None:
                nodes_info[key].weights[n] = 1

    @staticmethod
    def _reset_tables(tables):
        """
        Reset the Dijkstra tables for a new path search.

        :param dict(tuple(int,int),_DijkstraInfo) tables:
            the dictionary object for the Dijkstra-tables
        """
        for key in tables:
            tables[key] = _DijkstraInfo()

    def _propagate_costs_until_reached_destinations(
            self, tables, nodes_info, dest_chips, x_source, y_source):
        """
        Propagate the weights till the destination nodes of the source
        nodes are retraced.

        :param dict(tuple(int,int),_DijkstraInfo) tables:
            the dictionary object for the Dijkstra-tables
        :param dict(tuple(int,int),_NodeInfo) nodes_info:
            the dictionary object for the nodes inside a route scope
        :param set(tuple(int,int)) dest_chips:
        :param int x_source:
        :param int y_source:
        :raise PacmanRoutingException:
            when the destination node could not be reached from this source
            node
        """
        dest_chips_to_find = set(dest_chips)
        source = (x_source, y_source)
        dest_chips_to_find.discard(source)

        current = source

        # Iterate only if the destination node hasn't been activated
        while dest_chips_to_find:
            # PROPAGATE!
            for neighbour, weight in nodes_info[current].neighweights:
                # "neighbours" is a list of 6 links or None objects. There is
                # a None object where there is no connection to that neighbour
                if (neighbour is not None and
                        not (neighbour.destination_x == x_source and
                             neighbour.destination_y == y_source)):

                    # These variables change with every look at a new neighbour
                    self._update_neighbour(
                        tables, neighbour, current,
                        source, weight)

            # Set the next activated node as the deactivated node with the
            # lowest current cost
            current = self._minimum(tables)
            tables[current].activated = True
            dest_chips_to_find.discard(current)

    @staticmethod
    def _minimum(tables):
        """
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :rtype: tuple(int,int)
        """
        # This is the lowest cost across ALL deactivated nodes in the graph.
        lowest_cost = sys.maxsize
        lowest = None

        # Find the next node to be activated
        for key in tables:
            # Don't continue if the node hasn't even been touched yet
            if (tables[key].cost is not None and not tables[key].activated
                    and tables[key].cost < lowest_cost):
                lowest_cost = tables[key].cost
                lowest = key

        # If there were no deactivated nodes with costs, but the destination
        # was not reached this iteration, raise an exception
        if lowest is None:
            raise PacmanRoutingException(
                "Destination could not be activated, ending run")

        return int(lowest[0]), int(lowest[1])

    @staticmethod
    def _update_neighbour(tables, neighbour, current, source, weight):
        """
        Update the lowest cost for each neighbour_xy of a node.

        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :param ~spinn_machine.Link neighbour:
        :param tuple(int,int) current:
        :param tuple(int,int) source:
        :param float weight:
        :raise PacmanRoutingException: when the algorithm goes to a node that
            doesn't exist in the machine or the node's cost was set too low.
        """
        neighbour_xy = (neighbour.destination_x, neighbour.destination_y)
        if neighbour_xy not in tables:
            raise PacmanRoutingException(
                f"Tried to propagate to ({neighbour.destination_x}, "
                f"{neighbour.destination_y}), which is not in the"
                " graph: remove non-existent neighbours")

        chip_cost = tables[current].cost
        neighbour_cost = tables[neighbour_xy].cost

        # Only try to update if the neighbour_xy is within the graph and the
        # cost if the node hasn't already been activated and the lowest cost
        # if the new cost is less, or if there is no current cost.
        new_weight = float(chip_cost + weight)
        if (not tables[neighbour_xy].activated and
                (neighbour_cost is None or new_weight < neighbour_cost)):
            # update Dijkstra table
            tables[neighbour_xy].cost = new_weight

        if tables[neighbour_xy].cost == 0 and neighbour_xy != source:
            raise PacmanRoutingException(
                f"!!!Cost of non-source node ({neighbour.destination_x}, "
                f"{neighbour.destination_y}) was set to zero!!!")

    def _retrace_back_to_source(
            self, dest_xy, dest_cores, dest_links, tables, nodes_info,
            source_processor, source_link, pre_vertex, partition_id):
        """
        :param Placement dest: Destination placement
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :param MachineEdge edge:
        :param dict(tuple(int,int),_NodeInfo) nodes_info:
        :param int source_processor:
        :param int source_link:
        :return: the next coordinates to look into
        :rtype: tuple(int, int)
        :raise PacmanRoutingException:
            when the algorithm doesn't find a next point to search from. AKA,
            the neighbours of a chip do not have a cheaper cost than the node
            itself, but the node is not the destination or when the algorithm
            goes to a node that's not considered in the weighted search.
        """
        # Set the tracking node to the destination to begin with
        x, y = dest_xy

        entry = MulticastRoutingTableByPartitionEntry(
            dest_links, dest_cores)
        self._routing_paths.add_path_entry(
            entry, x, y, pre_vertex, partition_id)
        prev_entry = entry

        while tables[x, y].cost != 0:
            for idx, neighbour in enumerate(nodes_info[x, y].neighbours):
                if neighbour is not None:
                    n_xy = (neighbour.destination_x, neighbour.destination_y)

                    # Only check if it can be a preceding node if it actually
                    # exists
                    if n_xy not in tables:
                        raise PacmanRoutingException(
                            "Tried to trace back to node not in "
                            "graph: remove non-existent neighbours")

                    if tables[n_xy].cost is not None:
                        x, y, prev_entry, added = self._create_routing_entry(
                            n_xy, tables, idx, nodes_info, x, y,
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
        return x, y

    def _create_routing_entry(
            self, neighbour_xy, tables, neighbour_index,
            nodes_info, x, y, previous_entry, pre_vertex, partition_id):
        """
        Create a new routing entry.

        :param tuple(int,int) neighbour_xy:
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :param int neighbour_index:
        :param dict(tuple(int,int),_NodeInfo) nodes_info:
        :param int x:
        :param int y:
        :param MulticastRoutingTableByPartitionEntry previous_entry:
        :return: x, y, previous_entry, made_an_entry
        :rtype: tuple(int, int, MulticastRoutingTableByPartitionEntry, bool)
        :raise PacmanRoutingException:
            when the bandwidth of a router is beyond expected parameters
        """

        # Set the direction of the routing other_entry as that which is from
        # the preceding node to the current tracking node.
        # neighbour_xy is the 'old' coordinates since it is from the preceding
        # node. x and y are the 'new' coordinates since they are where the
        # router should send the packet to.
        dec_direction = self._get_reverse_direction(neighbour_index)
        made_an_entry = False

        neighbour_weight = nodes_info[neighbour_xy].weights[dec_direction]
        chip_sought_cost = tables[x, y].cost - neighbour_weight
        neighbours_lowest_cost = tables[neighbour_xy].cost

        if (neighbours_lowest_cost is not None and
                self._close_enough(neighbours_lowest_cost, chip_sought_cost)):
            # build the multicast entry
            entry = MulticastRoutingTableByPartitionEntry(
                dec_direction, None)
            previous_entry.incoming_link = neighbour_index
            # add entry for next hop going backwards into path
            self._routing_paths.add_path_entry(
                entry, neighbour_xy[0], neighbour_xy[1], pre_vertex,
                partition_id)
            previous_entry = entry
            made_an_entry = True

            # Finally move the tracking node
            x, y = neighbour_xy

        return x, y, previous_entry, made_an_entry

    @staticmethod
    def _close_enough(v1, v2, delta=0.00000000001):
        """
        :param float v1:
        :param float v2:
        :param float delta: How close values have to be to be "equal"
        """
        return abs(v1 - v2) < delta

    @staticmethod
    def _get_reverse_direction(neighbour_position):
        """
        Determine the direction of a link to go down.

        :param int neighbour_position: the position the neighbour is at
        :return: The position of the opposite link
        :rtype: int
        """

        if neighbour_position == 0:
            return 3
        elif neighbour_position == 1:
            return 4
        elif neighbour_position == 2:
            return 5
        elif neighbour_position == 3:
            return 0
        elif neighbour_position == 4:
            return 1
        elif neighbour_position == 5:
            return 2
        return None
