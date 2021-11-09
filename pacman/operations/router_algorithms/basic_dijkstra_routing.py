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

import logging
import sys
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar, DummyProgressBar
from pacman.exceptions import PacmanRoutingException
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry)

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


def basic_dijkstra_routing(placements, machine, machine_graph,
                 bw_per_route_entry=BW_PER_ROUTE_ENTRY, max_bw=MAX_BW):
    """ Find routes between the edges with the allocated information,
        placed in the given places

    :param Placements placements: The placements of the edges
    :param ~spinn_machine.Machine machine:
        The machine through which the routes are to be found
    :param MachineGraph machine_graph: the machine_graph object
    :param bool use_progress_bar: whether to show a progress bar
    :return: The discovered routes
    :rtype: MulticastRoutingTables
    :raise PacmanRoutingException:
        If something goes wrong with the routing
    """
    router = _BasicDijkstraRouting(machine, bw_per_route_entry, max_bw)
    return router(placements, machine_graph)


class _BasicDijkstraRouting(object):
    """ An routing algorithm that can find routes for edges between vertices\
        in a machine graph that have been placed on a machine by the use of a\
        Dijkstra shortest path algorithm.
    """

    __slots__ = [
        # the routing path objects used to be returned to the work flow
        "_routing_paths",

        # parameter to control ...........
        "_bw_per_route_entry",

        # parameter to control ...........
        "_max_bw",

        # the SpiNNMachine object used within the system.
        "_machine"
    ]

    def __init__(self, machine, bw_per_route_entry, max_bw):
        # set up basic data structures
        self._routing_paths = MulticastRoutingTableByPartition()
        self._bw_per_route_entry = bw_per_route_entry
        self._max_bw = max_bw
        self._machine = machine

    def _run(self, placements, machine_graph):
        """ Find routes between the edges with the allocated information,
            placed in the given places

        :param Placements placements: The placements of the edges
        :param ~spinn_machine.Machine machine:
            The machine through which the routes are to be found
        :param MachineGraph machine_graph: the machine_graph object
        :param bool use_progress_bar: whether to show a progress bar
        :return: The discovered routes
        :rtype: MulticastRoutingTables
        :raise PacmanRoutingException:
            If something goes wrong with the routing
        """

        nodes_info = self._initiate_node_info()
        tables = self._initiate_dijkstra_tables()
        self._update_all_weights(nodes_info)

        # each vertex represents a core in the board
        progress = ProgressBar(
            placements.n_placements, "Creating routing entries")

        for placement in progress.over(placements.placements):
            self._route(placement, placements, machine_graph,
                        nodes_info, tables)
        return self._routing_paths

    def _route(self, placement, placements, graph, node_info, tables):
        """
        :param Placement placement:
        :param Placements placements:
        :param MachineGraph graph:
        :param dict(tuple(int,int),_NodeInfo) node_info:
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        """
        # pylint: disable=too-many-arguments
        out_going_edges = (
            edge
            for edge in graph.get_edges_starting_at_vertex(placement.vertex)
            if edge.traffic_type == EdgeTrafficType.MULTICAST)

        dest_chips = set()
        edges_to_route = list()

        for edge in out_going_edges:
            destination = edge.post_vertex
            dest_place = placements.get_placement_of_vertex(destination)
            chip = self._machine.get_chip_at(dest_place.x, dest_place.y)
            dest_chips.add((chip.x, chip.y))
            edges_to_route.append(edge)

        if dest_chips:
            self._update_all_weights(node_info)
            self._reset_tables(tables)
            tables[placement.x, placement.y].activated = True
            tables[placement.x, placement.y].cost = 0
            self._propagate_costs_until_reached_destinations(
                tables, node_info, dest_chips, placement.x, placement.y)

        for edge in edges_to_route:
            dest = edge.post_vertex
            dest_placement = placements.get_placement_of_vertex(dest)
            self._retrace_back_to_source(
                dest_placement, tables, edge, node_info, placement.p, graph)

    def _initiate_node_info(self):
        """ Set up a dictionary which contains data for each chip in the\
            machine

        :return: nodes_info dictionary
        :rtype: dict(tuple(int,int),_NodeInfo)
        """
        nodes_info = dict()
        for chip in self._machine.chips:
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
        """ Set up the Dijkstra's table which includes if you've reached a\
            given node

        :return: the  Dijkstra's table dictionary
        :rtype: dict(tuple(int,int),_DijkstraInfo)
        """
        # Holds all the information about nodes within one full run of
        # Dijkstra's algorithm
        tables = dict()
        for chip in self._machine.chips:
            tables[chip.x, chip.y] = _DijkstraInfo()
        return tables

    def _update_all_weights(self, nodes_info):
        """ Change the weights of the neighbouring nodes

        :param dict(tuple(int,int),_NodeInfo) nodes_info:
            the node info dictionary
        """
        for key in nodes_info:
            if nodes_info[key] is not None:
                self._update_neighbour_weights(nodes_info, key)

    def _update_neighbour_weights(self, nodes_info, key):
        """ Change the weights of the neighbouring nodes

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
        """ Reset the Dijkstra tables for a new path search

        :param dict(tuple(int,int),_DijkstraInfo) tables:
            the dictionary object for the Dijkstra-tables
        """
        for key in tables:
            tables[key] = _DijkstraInfo()

    def _propagate_costs_until_reached_destinations(
            self, tables, nodes_info, dest_chips, x_source, y_source):
        """ Propagate the weights till the destination nodes of the source\
            nodes are retraced

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
        """ Update the lowest cost for each neighbour_xy of a node

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
                "Tried to propagate to ({}, {}), which is not in the"
                " graph: remove non-existent neighbours"
                .format(neighbour.destination_x, neighbour.destination_y))

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
                "!!!Cost of non-source node ({}, {}) was set to zero!!!"
                .format(neighbour.destination_x, neighbour.destination_y))

    def _retrace_back_to_source(
            self, dest, tables, edge, nodes_info, source_processor, graph):
        """
        :param Placement dest: Destination placement
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :param MachineEdge edge:
        :param dict(tuple(int,int),_NodeInfo) nodes_info:
        :param int source_processor:
        :param MachineGraph graph:
        :return: the next coordinates to look into
        :rtype: tuple(int, int)
        :raise PacmanRoutingException:
            when the algorithm doesn't find a next point to search from. AKA,
            the neighbours of a chip do not have a cheaper cost than the node
            itself, but the node is not the destination or when the algorithm
            goes to a node that's not considered in the weighted search.
        """
        # Set the tracking node to the destination to begin with
        x, y = dest.x, dest.y
        routing_entry_route_processors = []

        # if the processor is None, don't add to router path entry
        if dest.p is not None:
            routing_entry_route_processors.append(dest.p)
        routing_entry_route_links = None

        # build the multicast entry
        partitions = graph.get_multicast_edge_partitions_starting_at_vertex(
            edge.pre_vertex)

        prev_entry = None
        for partition in partitions:
            if edge in partition:
                entry = MulticastRoutingTableByPartitionEntry(
                    out_going_links=routing_entry_route_links,
                    outgoing_processors=routing_entry_route_processors)
                self._routing_paths.add_path_entry(
                    entry, dest.x, dest.y, partition)
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
                            prev_entry, edge, graph)
                        if added:
                            break
            else:
                raise PacmanRoutingException(
                    "Iterated through all neighbours of tracking node but"
                    " did not find a preceding node! Consider increasing "
                    "acceptable discrepancy between sought traceback cost"
                    " and actual cost at node. Terminating...")
        prev_entry.incoming_processor = source_processor
        return x, y

    def _create_routing_entry(
            self, neighbour_xy, tables, neighbour_index,
            nodes_info, x, y, previous_entry, edge, graph):
        """ Create a new routing entry

        :param tuple(int,int) neighbour_xy:
        :param dict(tuple(int,int),_DijkstraInfo) tables:
        :param int neighbour_index:
        :param dict(tuple(int,int),_NodeInfo) nodes_info:
        :param int x:
        :param int y:
        :param MulticastRoutingTableByPartitionEntry previous_entry:
        :param MachineEdge edge:
        :param MachineGraph graph:
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
            partns = graph.get_multicast_edge_partitions_starting_at_vertex(
                    edge.pre_vertex)
            entry = None
            for partition in partns:
                if edge in partition:
                    entry = MulticastRoutingTableByPartitionEntry(
                        dec_direction, None)
                    previous_entry.incoming_link = neighbour_index
                    # add entry for next hop going backwards into path
                    self._routing_paths.add_path_entry(
                        entry, neighbour_xy[0], neighbour_xy[1], partition)
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
        """ Determine the direction of a link to go down

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
