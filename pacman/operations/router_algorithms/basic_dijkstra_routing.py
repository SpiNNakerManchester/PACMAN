from spinn_utilities.progress_bar import ProgressBar

# pacman imports
from pacman import exceptions
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.model.routing_table_by_partition import \
    MulticastRoutingTableByPartition, MulticastRoutingTableByPartitionEntry

# general imports
import logging


logger = logging.getLogger(__name__)


class BasicDijkstraRouting(object):
    """ An routing algorithm that can find routes for edges between\
        vertices in a machine graph that have been placed on a
        machine by the use of a Dijkstra shortest path algorithm
    """

    __slots__ = [
        # the routing path objects used to be returned to the work flow
        "_routing_paths",

        # parameter to control ...........
        "_k",

        # parameter to control ...........
        "_l",

        # parameter to control ...........
        "_m",

        # parameter to control ...........
        "_bw_per_route_entry",

        # parameter to control ...........
        "_max_bw",

        # the SpiNNMachine object used within the system.
        "_machine"
    ]

    BW_PER_ROUTE_ENTRY = 0.01
    MAX_BW = 250

    def __call__(self, placements, machine, machine_graph, k=1, l=0, m=0,
                 bw_per_route_entry=BW_PER_ROUTE_ENTRY, max_bw=MAX_BW):
        """ Find routes between the edges with the allocated information,
            placed in the given places

        :param placements: The placements of the edges
        :type placements:\
            :py:class:`pacman.model.placements.placements.Placements`
        :param machine: The machine through which the routes are to be found
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param machine_graph: the machine_graph object
        :type machine_graph:\
            :py:class:`pacman.model.graph.machine_graph.MachineGraph`
        :return: The discovered routes
        :rtype:\
            :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """

        # set up basic data structures
        self._routing_paths = MulticastRoutingTableByPartition()
        self._k = k
        self._l = l
        self._m = m
        self._bw_per_route_entry = bw_per_route_entry
        self._max_bw = max_bw
        self._machine = machine

        nodes_info = self._initiate_node_info(machine)
        dijkstra_tables = self._initiate_dijkstra_tables(machine)
        self._update_all_weights(nodes_info, machine)

        # each vertex represents a core in the board
        progress = ProgressBar(placements.placements,
                               "Creating routing entries")

        for placement in progress.over(placements.placements):
            vertex = placement.vertex
            out_going_edges = \
                machine_graph.get_edges_starting_at_vertex(vertex)
            out_going_edges = \
                filter(
                    lambda application_edge:
                    application_edge.traffic_type == EdgeTrafficType.MULTICAST,
                    out_going_edges)

            dest_chips = set()
            edges_to_route = list()

            for edge in out_going_edges:
                destination = edge.post_vertex
                destination_placement = placements.get_placement_of_vertex(
                    destination)

                chip = machine.get_chip_at(destination_placement.x,
                                           destination_placement.y)
                dest_chips.add((chip.x, chip.y))
                edges_to_route.append(edge)

            if len(dest_chips) != 0:
                self._update_all_weights(nodes_info, machine)
                self._reset_tables(dijkstra_tables)
                dijkstra_tables[
                    (placement.x, placement.y)]["activated?"] = True
                dijkstra_tables[(placement.x, placement.y)]["lowest cost"] = 0
                self._propagate_costs_until_reached_destinations(
                    dijkstra_tables, nodes_info, dest_chips, placement.x,
                    placement.y)

            for edge in edges_to_route:
                dest = edge.post_vertex
                dest_placement = placements.get_placement_of_vertex(dest)
                self._retrace_back_to_source(
                    dest_placement.x, dest_placement.y, dijkstra_tables,
                    dest_placement.p, edge, nodes_info, placement.p,
                    machine_graph)
        return self._routing_paths

    def _initiate_node_info(self, machine):
        """ Set up a dictionary which contains data for each chip in the\
            machine

        :param machine: the machine object
        :type machine: spinn_machine.machine.Machine
        :return: nodes_info dictionary
        :rtype: dict
        :raise None: this method does not raise any known exceptions
        """
        nodes_info = dict()
        for chip in machine.chips:
            x, y = chip.x, chip.y

            # get_neighbours should return a list of
            # dictionaries of 'x' and 'y' values
            nodes_info[(x, y)] = dict()

            nodes_info[(x, y)]["neighbours"] = list()
            for source_id in range(6):
                nodes_info[(x, y)]["neighbours"].append(
                    chip.router.get_link(source_id))

            nodes_info[(x, y)]["bws"] = []

            nodes_info[(x, y)]["weights"] = []

            for i in range(len(nodes_info[(x, y)]["neighbours"])):

                nodes_info[(x, y)]["weights"].append(None)

                if nodes_info[(x, y)]["neighbours"][i] is None:

                    nodes_info[(x, y)]["bws"].append(None)

                else:

                    nodes_info[(x, y)]["bws"].append(self._max_bw)
        return nodes_info

    @staticmethod
    def _initiate_dijkstra_tables(machine):
        """ Set up the Dijkstra's table which includes if you've reached a \
            given node

        :param machine: the machine object
        :type machine: the spinn_machine.machine.Machine object
        :return: the  Dijkstra's table dictionary
        :rtype: dict
        :raise None: this method does not raise any known exception
        """
        # Holds all the information about nodes within one full run of
        # Dijkstra's algorithm
        dijkstra_tables = dict()

        for chip in machine.chips:
            x, y = chip.x, chip.y

            # Each node has a dictionary, or 'table'
            dijkstra_tables[(x, y)] = dict()

            dijkstra_tables[(x, y)]["lowest cost"] = None
            dijkstra_tables[(x, y)]["activated?"] = False
        return dijkstra_tables

    def _update_all_weights(self, nodes_info, machine):
        """ Change the weights of the neighbouring nodes

        :param nodes_info: the node info dictionary
        :type nodes_info: dict
        :param machine: the machine python object that represents the\
                    structure of the machine
        :type machine: 'py:class':spinn_machine.machine.Machine
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        for key in nodes_info:
            if nodes_info[key] is not None:
                self._update_neighbour_weights(nodes_info, machine, key)

    def _update_neighbour_weights(self, nodes_info, machine, key):
        """ Change the weights of the neighbouring nodes

        :param nodes_info: the node info dictionary
        :param machine: the machine python object that represents the\
                    structure of the machine
        :param key: the identifier to the object in nodes_info
        :type key: str
        :type nodes_info: dict
        :type machine: 'py:class':spinn_machine.machine.Machine
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        for n in range(len(nodes_info[key]["neighbours"])):
            if nodes_info[key]["neighbours"][n] is not None:
                neighbour = nodes_info[key]["neighbours"][n]
                xn, yn = neighbour.destination_x, neighbour.destination_y
                entries = self._routing_paths.get_entries_for_router(xn, yn)
                nodes_info[key]["weights"][n] = self._get_weight(
                    machine.get_chip_at(xn, yn).router,
                    nodes_info[key]["bws"][n],
                    len(entries))

    def _get_weight(self, router, bws, no_routing_table_entries):
        """ Get the weight based on basic heuristics

        :param router: the router to assess the weight of
        :param bws: the basic weight of the source node
        :param no_routing_table_entries: the number of entries going though\
                this router
        :type router: spinn_machine.router.Router
        :type bws: int
        :type no_routing_table_entries: int
        :return: weight of this router
        :rtype: int
        :raise None: does not raise any known exception
        """
        free_entries = (router.ROUTER_DEFAULT_AVAILABLE_ENTRIES -
                        no_routing_table_entries)

        q = 0
        if self._l > 0:
            q = float(self._l *
                      (1 / float(free_entries) - 1 /
                       float(router.ROUTER_DEFAULT_AVAILABLE_ENTRIES)))

        t = 0
        if self._m > 0:
            t = self._m * (1 / float(bws) - 1 / float(self._max_bw))

        weight = self._k + q + t
        return weight

    @staticmethod
    def _reset_tables(dijkstra_tables):
        """ Reset the Dijkstra tables for a new path search

        :param dijkstra_tables: the dictionary object for the Dijkstra-tables
        :type dijkstra_tables: dict
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        for key in dijkstra_tables:
            dijkstra_tables[key]["lowest cost"] = None
            dijkstra_tables[key]["activated?"] = False

    def _propagate_costs_until_reached_destinations(
            self, dijkstra_tables, nodes_info, dest_chips,
            x_source, y_source):
        """ Propagate the weights till the destination nodes of the source\
            nodes are retraced

         :param dijkstra_tables: the dictionary object for the Dijkstra-tables
         :param nodes_info: the dictionary object for the nodes inside a route\
                    scope
         :param dest_chips:
         :param x_source:
         :param y_source:
         :type dijkstra_tables: dict
         :type nodes_info: dict
         :type dest_chips:
         :type x_source: int
         :type y_source: int
         :rtype: None
         :raise PacmanRoutingException: when the destination node could not be\
                    reached from this source node.
        """

        dest_chips_to_find = set(dest_chips)
        try:
            dest_chips_to_find.remove((x_source, y_source))
        except KeyError:
            # Ignore this - it just isn't in the set of destinations
            pass

        x_current = x_source
        y_current = y_source

        # Iterate only if the destination node hasn't been activated
        while len(dest_chips_to_find) > 0:

            # PROPAGATE!
            for i in range(len(
                    nodes_info[(x_current, y_current)]["neighbours"])):
                neighbour = nodes_info[(x_current, y_current)]["neighbours"][i]
                weight = nodes_info[(x_current, y_current)]["weights"][i]

                # "neighbours" is a list of 6 links or None objects.
                # There is a None object where there is no connection to
                # that neighbour.
                if ((neighbour is not None) and
                        not (neighbour.destination_x == x_source and
                             neighbour.destination_y == y_source)):

                    # These variables change with every look at a new neighbour
                    self._update_neighbour(
                        dijkstra_tables, neighbour.destination_x,
                        neighbour.destination_y, x_current, y_current,
                        x_source, y_source, weight)

            # This is the lowest cost across ALL
            # deactivated nodes in the graph.
            graph_lowest_cost = None

            # Find the next node to be activated
            for key in dijkstra_tables:

                # Don't continue if the node hasn't even been touched yet
                if (dijkstra_tables[key]["lowest cost"] is not None and
                        not dijkstra_tables[key]["activated?"] and
                        (graph_lowest_cost is not None and
                         (dijkstra_tables[key]["lowest cost"] <
                          graph_lowest_cost) or graph_lowest_cost is None)):
                    graph_lowest_cost = dijkstra_tables[key]["lowest cost"]
                    x_current, y_current = int(key[0]), int(key[1])

            # If there were no deactivated nodes with costs,
            # but the destination was not reached this iteration,
            # raise an exception
            if graph_lowest_cost is None:
                raise exceptions.PacmanRoutingException(
                    "Destination could not be activated, ending run")

            # Set the next activated node as the deactivated node with the
            #  lowest current cost
            dijkstra_tables[(x_current, y_current)]["activated?"] = True
            try:
                dest_chips_to_find.remove((x_current, y_current))
            except KeyError:
                # Ignore the error - it just isn't a destination chip
                pass

    @staticmethod
    def _update_neighbour(
            dijkstra_tables, x_neighbour, y_neighbour, x_current, y_current,
            x_source, y_source, weight):
        """ Update the lowest cost for each neighbour of a node

        :rtype: None
        :raise PacmanRoutingException: when the algorithm goes to a node that\
                    doesn't exist in the machine or the node's cost was set\
                    too low.
        """
        neighbour_exists = (x_neighbour, y_neighbour) in dijkstra_tables
        if not neighbour_exists:
            raise exceptions.PacmanRoutingException(
                "Tried to propagate to ({}, {}), which is not in the"
                " graph: remove non-existent neighbours"
                .format(x_neighbour, y_neighbour))

        neighbour_activated =\
            dijkstra_tables[(x_neighbour, y_neighbour)]["activated?"]
        chip_lowest_cost =\
            dijkstra_tables[(x_current, y_current)]["lowest cost"]
        neighbour_lowest_cost =\
            dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"]

        # Only try to update if the neighbour is within the graph
        #  and the cost if the node hasn't already been activated
        # and the lowest cost if the new cost is less, or if
        # there is no current cost
        new_weight = float(chip_lowest_cost + weight)
        if (not neighbour_activated and
                (neighbour_lowest_cost is None or
                 new_weight < neighbour_lowest_cost)):

            # update Dijkstra table
            dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"] =\
                new_weight

        if (dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"] == 0) \
                and (x_neighbour != x_source or y_neighbour != y_source):
            raise exceptions.PacmanRoutingException(
                "!!!Cost of non-source node ({}, {}) was set to zero!!!"
                .format(x_neighbour, y_neighbour))

    def _retrace_back_to_source(
            self, x_destination, y_destination, dijkstra_tables,
            processor_dest, edge, nodes_info, source_processor,
            graph):
        """

        :param x_destination:
        :param y_destination:
        :param dijkstra_tables:
        :param processor_dest:
        :param edge:
        :param nodes_info:
        :type nodes_info:
        :type edge:
        :type x_destination:
        :type y_destination:
        :type dijkstra_tables:
        :type processor_dest:
        :param graph:
        :type graph:
        :return: the next coordinates to look into
        :rtype: int int
        :raise PacmanRoutingException: when the algorithm doesn't find a next\
                    point to search from. AKA, the neighbours of a chip do not\
                    have a cheaper cost than the node itself, but the node is\
                    not the destination or when the algorithm goes to a node\
                    that's not considered in the weighted search
        """
        # Set the tracking node to the destination to begin with
        x_current, y_current = x_destination, y_destination
        routing_entry_route_processors = []

        # if the processor is None, don't add to router path entry
        if processor_dest is not None:
            routing_entry_route_processors.append(processor_dest)
        routing_entry_route_links = None

        # build the multicast entry
        partitions = \
            graph.get_outgoing_edge_partitions_starting_at_vertex(
                edge.pre_vertex)

        previous_routing_entry = None
        for partition in partitions:
            if edge in partition:
                entry = MulticastRoutingTableByPartitionEntry(
                    out_going_links=routing_entry_route_links,
                    outgoing_processors=routing_entry_route_processors)

                self._routing_paths.add_path_entry(
                    entry, x_destination, y_destination, partition)
                previous_routing_entry = entry

        while dijkstra_tables[(x_current, y_current)]["lowest cost"] != 0:

            x_check, y_check = x_current, y_current

            neighbours = nodes_info[(x_current, y_current)]["neighbours"]
            neighbour_index = 0
            added_an_entry = False
            while not added_an_entry and neighbour_index < len(neighbours):
                neighbour = neighbours[neighbour_index]
                if neighbour is not None:

                    x_neighbour, y_neighbour = (neighbour.destination_x,
                                                neighbour.destination_y)

                    # Only check if it can be a preceding node if it actually
                    # exists
                    if (x_neighbour, y_neighbour) in dijkstra_tables:
                        dijkstra_table_key = (x_neighbour, y_neighbour)
                        lowest_cost = \
                            dijkstra_tables[dijkstra_table_key]["lowest cost"]
                        if lowest_cost is not None:
                            (x_current, y_current, previous_routing_entry,
                                added_an_entry) = self._create_routing_entry(
                                    x_neighbour, y_neighbour, dijkstra_tables,
                                    neighbour_index, nodes_info,
                                    x_current, y_current,
                                    previous_routing_entry, edge,
                                    graph)
                    else:
                        raise exceptions.PacmanRoutingException(
                            "Tried to trace back to node not in "
                            "graph: remove non-existent"
                            " neighbours")
                neighbour_index += 1

            if x_current == x_check and y_current == y_check:
                raise exceptions.PacmanRoutingException(
                    "Iterated through all neighbours of tracking node but"
                    " did not find a preceding node! Consider increasing "
                    "acceptable discrepancy between sought traceback cost"
                    " and actual cost at node. Terminating...")
        previous_routing_entry.incoming_processor = source_processor
        return x_current, y_current

    def _create_routing_entry(
            self, x_neighbour, y_neighbour, dijkstra_tables, neighbour_index,
            nodes_info, x_current, y_current, previous_routing_entry, edge,
            graph):
        """ Create a new routing entry

        :return: x_current, y_current, previous_routing_entry, made_an_entry
        :rtype: int, int, spinn_machine.multicast_routing_entry, bool
        :raise PacmanRoutingException: when the bandwidth of a router is\
                beyond expected parameters
        """

        # Set the direction of the routing other_entry as that which
        # is from the preceding node to the current tracking node
        # x_neighbour, y_neighbour are the 'old' coordinates since they are
        # from the preceding node. x_current and y_current are the 'new'
        # coordinates since they are where the router should send the packet to
        dec_direction = self._get_reverse_direction(neighbour_index)
        made_an_entry = False

        neighbour_weight = \
            nodes_info[(x_neighbour, y_neighbour)]["weights"][dec_direction]
        chip_sought_cost = \
            (dijkstra_tables[(x_current, y_current)]["lowest cost"] -
             neighbour_weight)
        neighbours_lowest_cost = \
            dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"]

        if (neighbours_lowest_cost is not None and
                abs(neighbours_lowest_cost - chip_sought_cost) <
                0.00000000001):

            # build the multicast entry
            partitions = graph.\
                get_outgoing_edge_partitions_starting_at_vertex(
                    edge.pre_vertex)
            entry = None
            for partition in partitions:
                if edge in partition:
                    entry = MulticastRoutingTableByPartitionEntry(
                        out_going_links=dec_direction,
                        outgoing_processors=None)
                    previous_routing_entry.incoming_link = neighbour_index
                    # add entry for next hop going backwards into path
                    self._routing_paths.add_path_entry(
                        entry, x_neighbour, y_neighbour, partition)
            previous_routing_entry = entry
            made_an_entry = True

            # Finally move the tracking node
            x_current, y_current = x_neighbour, y_neighbour

        return x_current, y_current, previous_routing_entry, made_an_entry

    @staticmethod
    def _get_reverse_direction(neighbour_position):
        """ Determine the direction of a link to go down

        :param neighbour_position: the position the neighbour is at
        :type neighbour_position: int
        :return: The position of the opposite link
        :rtype: int
        :raise None: this method does not raise any known exceptions
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
