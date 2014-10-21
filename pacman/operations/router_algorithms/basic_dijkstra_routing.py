from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.operations.router_algorithms.abstract_router_algorithm \
    import AbstractRouterAlgorithm
from pacman.utilities.progress_bar import ProgressBar
from pacman import exceptions

import logging
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

logger = logging.getLogger(__name__)


class BasicDijkstraRouting(AbstractRouterAlgorithm):
    """ An routing algorithm that can find routes for subedges between\
        subvertices in a partitioned_graph that have been placed on a
        machine by the use of a dijkstra shortest path algorithm
    """

    BW_PER_ROUTE_ENTRY = 0.01
    MAX_BW = 250

    def __init__(self, k=1, l=0, m=0, bw_per_route_entry=BW_PER_ROUTE_ENTRY,
                 max_bw=MAX_BW):
        """constructor for the
        pacman.operations.router_algorithms.DijkstraRouting.DijkstraRouting

        <params to be implemented when done>
        """
        AbstractRouterAlgorithm.__init__(self)
        self._k = k
        self._l = l
        self._m = m
        self._bw_per_route_entry = bw_per_route_entry
        self._max_bw = max_bw

    def route(self, routing_info_allocation, placements, machine,
              partitioned_graph):
        """ Find routes between the subedges with the allocated information,
            placed in the given places

        :param routing_info_allocation: The allocated routing information
        :type routing_info_allocation:\
                :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :param placements: The placements of the subedges
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param machine: The machine through which the routes are to be found
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param partitioned_graph: the partitioned_graph object
        :type partitioned_graph:
        pacman.partitioned_graph.partitioned_graph.PartitionedGraph
        :return: The discovered routes
        :rtype: :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """
        #set up basic data structures
        nodes_info = self._initiate_node_info(machine)
        dijkstra_tables = self._initiate_dijkstra_tables(machine)
        self._update_all_weights(nodes_info, machine)

        # each subvertex represents a core in the board
        progress = ProgressBar(len(list(placements.placements)),
                               "on creating routing entries for each subvertex")

        for placement in placements.placements:
            subvert = placement.subvertex
            out_going_sub_edges = \
                partitioned_graph.outgoing_subedges_from_subvertex(subvert)

            dest_chips = set()
            subedges_to_route = list()

            for subedge in out_going_sub_edges:
                destination_subvetex = subedge.post_subvertex
                destination_placement = \
                    placements.get_placement_of_subvertex(destination_subvetex)

                chip = machine.get_chip_at(destination_placement.x,
                                           destination_placement.y)
                dest_chips.add((chip.x, chip.y))
                subedges_to_route.append(subedge)

            if len(dest_chips) != 0:
                self._update_all_weights(nodes_info, machine)
                self._reset_tables(dijkstra_tables)
                dijkstra_tables[(placement.x, placement.y)]["activated?"] = True
                dijkstra_tables[(placement.x, placement.y)]["lowest cost"] = 0
                self._propagate_costs_until_reached_destinations(
                    dijkstra_tables, nodes_info, dest_chips, placement.x,
                    placement.y)

            for subedge in subedges_to_route:
                subedge_routing_info = \
                    routing_info_allocation.\
                    get_subedge_information_from_subedge(subedge)
                dest = subedge.post_subvertex
                placement = placements.get_placement_of_subvertex(dest)
                self._retrace_back_to_source(
                    placement.x, placement.y, nodes_info, dijkstra_tables,
                    subedge_routing_info, placement.p)
            progress.update()
        progress.end()
        return self._routing_tables

    def _initiate_node_info(self, machine):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used for setting up a dictionary which contains data for each chip in \
        the machine

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
        """ private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used to set up the Dijkstra's table which includes if you've reached a \
        given node

        :param machine: the machine object
        :type machine: the spinn_machine.machine.Machine object
        :return the  Dijkstra's table dictionary
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
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used by the routing algorithum to change the weights of the nebourign \
        nodes

        :param nodes_info: the node info dictonary
        :param machine: the machine python object that represnets the strcuture\
        of the machine
        :type nodes_info: dict
        :type machine 'py:class':spinn_machine.machine.Machine
        :return None
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        for key in nodes_info.keys():
            if nodes_info[key] is not None:
                self._update_neighbour_weights(nodes_info, machine, key)

    def _update_neighbour_weights(self, nodes_info, machine, key):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used by the routing algorithm to change the weights of the neighbouring\
        nodes

        :param nodes_info: the node info dictionary
        :param machine: the machine python object that represents the structure\
        of the machine
        :param key: the identifier to the object in nodes_info
        :type key: str
        :type nodes_info: dict
        :type machine 'py:class':spinn_machine.machine.Machine
        :return None
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        for n in range(len(nodes_info[key]["neighbours"])):
            if nodes_info[key]["neighbours"][n] is not None:
                neighbour = nodes_info[key]["neighbours"][n]
                xn, yn = neighbour.destination_x, neighbour.destination_y
                nodes_info[key]["weights"][n] = \
                    self._get_weight(
                        machine.get_chip_at(xn, yn).router,
                        nodes_info[key]["bws"][n],
                        self._get_routing_table_for_chip(xn, yn))

    def _get_routing_table_for_chip(self, chip_x, chip_y):
        """helper method to retrieve a routing table

        :param chip_x: the x coord for a chip
        :param chip_y: the y coord for a chip
        :type chip_x: int
        :type chip_y: int
        :return a routing table
        :rtype: pacman.routing_tables.RoutingTable
        :raise None: this method does not raise any known exception

        """
        table = self._routing_tables.get_routing_table_for_chip(chip_x, chip_y)
        if table is not None:
            return table
        else:
            chip_routing_table = MulticastRoutingTable(chip_x, chip_y)
            self._routing_tables.add_routing_table(chip_routing_table)
            return chip_routing_table

    def _get_weight(self, router, bws, routing_table):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used by the routing algorithm to determine the weight based on basic
        heuristics

        :param router: the router to assess the weight of
        :param bws: the basic weight of the source node
        :param routing_table: the routing table object for this router
        :type router: spinn_machine.router.Router
        :type bws: int
        :type routing_table:\
                    py:class:`pacman.model.routing_tables.multicast_routing_table.MulticastRoutingTable`
        :return weight of this router
        :rtype: int
        :raise None: does not raise any known exception
        """
        free_entries = \
            router.ROUTER_DEFAULT_AVAILABLE_ENTRIES - \
            routing_table.number_of_entries

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
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used to reset the dijsktra tables for a new path search

        :param dijkstra_tables: the dictory object for the dijkstra-tables
        :type dijkstra_tables: dict
        :return: None
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        for key in dijkstra_tables.keys():
            dijkstra_tables[key]["lowest cost"] = None
            dijkstra_tables[key]["activated?"] = False

    def _propagate_costs_until_reached_destinations(
            self, dijkstra_tables, nodes_info, dest_chips,
            x_source, y_source):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used to propagate the weights till the destination nodes of the source\
        nodes are reaced

         :param dijkstra_tables: the dictionary object for the dijkstra-tables
         :param nodes_info: the dictionary object for the nodes inside a route \
         scope
         :param dest_chips:
         :param x_source:
         :param y_source:
         :type dijkstra_tables: dict
         :type nodes_info: dict
         :type dest_chips:
         :type x_source: int
         :type y_source: int
         :return: None
         :rtype: None
         :raise PacmanRoutingException: when the destination node could not be\
         reached from this soruce node.
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
            for i in range(len(nodes_info[(x_current, y_current)]["neighbours"])):
                neighbour = nodes_info[(x_current, y_current)]["neighbours"][i]
                weight = nodes_info[(x_current, y_current)]["weights"][i]

                # "neighbours" is a list of 6 links or None objects.
                # There is a None object where there is no connection to
                # that neighbour.
                if ((neighbour is not None)
                        and not (neighbour.destination_x == x_source
                                 and neighbour.destination_y == y_source)):

                    # These variables change with every look at a new neighbour
                    self._update_neighbour(
                        dijkstra_tables, neighbour.destination_x,
                        neighbour.destination_y, x_current, y_current, x_source,
                        y_source, weight)

            # This cannot be done in the above loop, since when a node
            # becomes activated the rest of the costs cannot be retrieved, and
            #  a new partitionable_graph lowest cost cannot be found

            # This is the lowest cost across ALL
            # unactivated nodes in the partitionable_graph.
            graph_lowest_cost = None

            # Find the next node to be activated
            for key in dijkstra_tables.keys():

                # Don't continue if the node hasn't even been touched yet
                if (dijkstra_tables[key]["lowest cost"] is not None
                    and not dijkstra_tables[key]["activated?"]
                    and (graph_lowest_cost is not None
                    and dijkstra_tables[key]["lowest cost"] < graph_lowest_cost
                         or graph_lowest_cost is None)):
                            graph_lowest_cost = \
                                dijkstra_tables[key]["lowest cost"]
                            x_current, y_current = int(key[0]), int(key[1])

            # If there were no unactivated nodes with costs,
            # but the destination was not reached this iteration,
            # raise an exception
            if graph_lowest_cost is None:
                raise exceptions.PacmanRoutingException(
                    "Destination could not be activated, ending run")

            # Set the next activated node as the unactivated node with the
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
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used to update the lowest cost for each neigbhour of a node

        :param dijkstra_tables:
        :param x_current:
        :param y_current:
        :param x_source:
        :param y_source:
        :param x_neighbour:
        :param y_neighbour:
        :param weight:
        :type dijkstra_tables:
        :type x_current:
        :type y_current:
        :type x_source:
        :type y_source:
        :type x_neighbour:
        :type y_neighbour:
        :type weight:
        :return:
        :rtype:
        :raise PacmanRoutingException: when the algoerithum goes to a node that\
        doesnt exist in the machine or the node's cost was set too low.
        """
        neighbour_exists = (x_neighbour, y_neighbour) in dijkstra_tables
        if not neighbour_exists:
            raise exceptions.PacmanRoutingException(
                "Tried to propagate to ({}, {}), which is not in the"
                " partitionable_graph: remove non-existent neighbours"
                .format(x_neighbour, y_neighbour))

        neighbour_activated =\
            dijkstra_tables[(x_neighbour, y_neighbour)]["activated?"]
        chip_lowest_cost =\
            dijkstra_tables[(x_current, y_current)]["lowest cost"]
        neighbour_lowest_cost =\
            dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"]

        # Only try to update if the neighbour is within the partitionable_graph
        #  and the cost if the node hasn't already been activated
        # and the lowest cost if the new cost is less, or if
        # there is no current cost
        new_weight = float(chip_lowest_cost + weight)
        if (not neighbour_activated
                and (neighbour_lowest_cost is None
                     or new_weight < neighbour_lowest_cost)):

                #update dijkstra table
                dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"] =\
                    new_weight

        if (dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"] == 0) \
                and (x_neighbour != x_source or y_neighbour != y_source):
            raise exceptions.PacmanRoutingException(
                "!!!Cost of non-source node ({}, {}) was set to zero!!!"
                .format(x_neighbour, y_neighbour))

    def _retrace_back_to_source(self, x_destination, y_destination, nodes_info,
                                dijkstra_tables, subedge_routing_info,
                                processor_dest):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \

        :param x_destination:
        :param y_destination:
        :param nodes_info:
        :param dijkstra_tables:
        :param subedge_routing_info:
        :param processor_dest:
        :type x_destination:
        :type y_destination:
        :type nodes_info:
        :type dijkstra_tables:
        :type subedge_routing_info:
        :type processor_dest:
        :return: the next coords to look into
        :rtype: int int
        :raise PacmanRoutingException: when the algorithum doesnt find a next\
         point to search from. AKA, the neighbours of a chip do not have a \
         cheaper cost than the node itslef, but the node is not the destination\
         or when the algorithum goes to a node thats not cosndiered in the \
         weighted search
        """
        # Set the tracking node to the destination to begin with
        x_current, y_current = x_destination, y_destination
        routing_entry_route_processors = [processor_dest]
        routing_entry_route_links = list()

        #check that the key hasnt already been used
        key = subedge_routing_info.key_mask_combo
        mask = subedge_routing_info.mask
        routing_table = self._get_routing_table_for_chip(x_destination,
                                                         y_destination)
        #check if an other_entry with the same key mask combo exists
        other_entry = routing_table.get_multicast_routing_entry_by_key(key,
                                                                       mask)
        if other_entry is not None:
            merged_entry = \
                self._merge_entries(other_entry, routing_entry_route_processors,
                                    False, key, mask, routing_entry_route_links,
                                    routing_table)
            previous_routing_entry = merged_entry
        else:
            entry = MulticastRoutingEntry(key, mask,
                                          routing_entry_route_processors,
                                          routing_entry_route_links, False)
            routing_table.add_mutlicast_routing_entry(entry)
            previous_routing_entry = entry

        while dijkstra_tables[(x_current, y_current)]["lowest cost"] != 0:

            xcheck, ycheck = x_current, y_current

            neighbours = nodes_info[(x_current, y_current)]["neighbours"]
            neighbour_index = 0
            added_an_entry = False
            while not added_an_entry and neighbour_index < len(neighbours):
                neighbour = neighbours[neighbour_index]
                if neighbour is not None:

                    x_neighbour, y_neighbour = (neighbour.destination_x,
                                                neighbour.destination_y)
                    neighbour_routing_table = self._get_routing_table_for_chip(
                        x_neighbour, y_neighbour)

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
                                    neighbour_routing_table,
                                    x_current, y_current,
                                    subedge_routing_info,
                                    previous_routing_entry)
                    else:
                        raise exceptions.PacmanRoutingException(
                            "Tried to trace back to node not in "
                            "partitionable_graph: remove non-existent"
                            " neighbours")
                neighbour_index += 1

            if x_current == xcheck and y_current == ycheck:
                raise exceptions.PacmanRoutingException(
                    "Iterated through all neighbours of tracking node but"
                    " did not find a preceding node! Consider increasing "
                    "acceptable discrepancy between sought traceback cost"
                    " and actual cost at node. Terminating...")
        return x_current, y_current

    @staticmethod
    def _merge_entries(other_entry, routing_entry_route_processors, defaultable,
                       key, mask, routing_entry_route_links, routing_table):

        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \

        :param other_entry:
        :param routing_entry_route_processors:
        :param routing_entry_route_links:
        :param routing_table:
        :param defaultable:
        :param key:
        :param mask:
        :type other_entry:
        :type routing_entry_route_processors:
        :type routing_entry_route_links:
        :type routing_table:
        :type defaultable:
        :type key:
        :type mask:
        :return a new entry which is the merged result of two entries
        :rtype: spinn_machine.multicast_routing_entry
        :raise None: this method does not raise any known exception
        """

        multi_cast_routing_entry = \
            MulticastRoutingEntry(key, mask, routing_entry_route_processors,
                                  routing_entry_route_links, defaultable)
        new_entry = other_entry.merge(multi_cast_routing_entry)
        routing_table.remove_multicast_routing_entry(other_entry)
        routing_table.add_mutlicast_routing_entry(new_entry)
        return new_entry

    def _create_routing_entry(self, x_neighbour, y_neighbour, dijkstra_tables,
                              neighbour_index, nodes_info, router_table,
                              x_current, y_current, edge_info,
                              previous_routing_entry):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \

        :param x_neighbour:
        :param y_neighbour:
        :param dijkstra_tables:
        :param neighbour_index
        :param nodes_info:
        :param router_table:
        :param x_current:
        :param y_current:
        :param edge_info:
        :param previous_routing_entry:
        :type x_neighbour:
        :type y_neighbour:
        :type dijkstra_tables:
        :type neighbour_index
        :type nodes_info:
        :type router_table:
        :type x_current:
        :type y_current:
        :type edge_info:
        :type previous_routing_entry:
        :return x_current, y_current, previous_routing_entry, made_an_entry
        :rtype: int, int, spinn_machine.multicast_routing_entry, bool
        :raise PacmanRoutingException: when the bandwidth of a router is beyond\
        respectable parameters
        """

        # Set the direction of the routing other_entry as that which
        # is from the preceding node to the current tracking node
        # x_neighbour, y_neighbour are the 'old' coordinates since they are from the
        # preceding node. x_current and y_current are the 'new' coordinates since
        # they are where the router should send the packet to
        dec_direction = self._get_reverse_direction(neighbour_index)
        made_an_entry = False

        #determine if this entry is going to be defaultable
        entry_is_defaultable = False
        if dec_direction in previous_routing_entry.link_ids:
            entry_is_defaultable = True

        neighbour_weight = nodes_info[(x_neighbour, y_neighbour)]["weights"][dec_direction]
        chip_sought_cost = \
            dijkstra_tables[(x_current, y_current)]["lowest cost"] - neighbour_weight
        neighbours_lowest_cost = dijkstra_tables[(x_neighbour, y_neighbour)]["lowest cost"]
        #print ("Checking node (%d, %d) with sought cost %s and actual
        # cost %s") % (x_neighbour, y_neighbour, chip_sought_cost,
        # dijkstra_tables[x_neighbour][y_neighbour]["lowest cost"])

        if (neighbours_lowest_cost is not None
                and abs(neighbours_lowest_cost - chip_sought_cost) <
                0.00000000001):

            #get other routing table and entry
            other_routing_table = \
                self._get_routing_table_for_chip(x_neighbour, y_neighbour)
            edge_key, edge_mask = edge_info.key_combo, edge_info.mask
            other_routing_table_entry = other_routing_table.\
                get_multicast_routing_entry_by_key(edge_key, edge_mask)
            if other_routing_table_entry is not None:

                #already has an other_entry, check if mergable,
                #  if not then throw error, therefore should only ever
                # have 1 other_entry
                if other_routing_table_entry.key_combo == edge_key:

                    #merge routes
                    merged_entry = self._merge_entries(
                        other_routing_table_entry, (), entry_is_defaultable,
                        edge_key, edge_mask, [dec_direction],
                        router_table)
                    previous_routing_entry = merged_entry
            else:
                entry = MulticastRoutingEntry(
                    edge_key, edge_mask, (), [dec_direction],
                    entry_is_defaultable)
                router_table.add_mutlicast_routing_entry(entry)
                previous_routing_entry = entry
            made_an_entry = True

            # Finally move the tracking node
            x_current, y_current = x_neighbour, y_neighbour

            nodes_info[(x_neighbour, y_neighbour)]["bws"][dec_direction] -= \
                self._bw_per_route_entry  # TODO arbitrary

            if nodes_info[(x_neighbour, y_neighbour)]["bws"][dec_direction] < 0:
                print ("Bandwidth overused from ({}, {}) in direction {}! to "
                       "({}, {})".format(x_neighbour, y_neighbour,
                                         dec_direction, x_current, y_current))

                raise exceptions.PacmanRoutingException(
                    "Bandwidth overused as described above! Terminating...")
        return x_current, y_current, previous_routing_entry, made_an_entry

    @staticmethod
    def _get_reverse_direction(neighbour_position):
        """private method, do not call from outside dijskra routing\

        used to detmerine the direction of a link to go down

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

    @staticmethod
    def _has_same_route(processors, links, entry):
        """ private method, not to be called outside dijskra routing

        :param processors: the list of processors that a routing entry has gone\
         down
        :param links: the list of links to which a routing entry has gone down
        :param entry: the other entry to compare against
        :type processors: list of ints
        :type links: list of ints
        :type entry: spinn_machine.multicast_routing_entry.MultcastRoutingEntry
        :return true if the links and processors are the same \
        (same outgoing route)
        :rtype: bool
        :raise None: this method does not raise any known exception

        """
        if entry.processors_ids == processors and entry.link_ids == links:
            return True
        else:
            return False