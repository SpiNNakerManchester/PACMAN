from pacman.operations.router_algorithms.abstract_router_algorithm \
    import AbstractRouterAlgorithm
from pacman.utilities.progress_bar import ProgressBar

import logging
logger = logging.getLogger(__name__)


class BasicDijkstraRouting(AbstractRouterAlgorithm):
    """ An routing algorithm that can find routes for subedges between\
        subvertices in a subgraph that have been placed on a machine by the use
        of a dijkstra shortest path algorithm
    """

    BW_PER_ROUTE_ENTRY = 0.01
    MAX_BW = 250

    def __init__(self, k=1, l=0, m=0, bw_per_route_entry=BW_PER_ROUTE_ENTRY,
                 max_bw=MAX_BW):
        """constructor for the
        pacman.operations.router_algorithms.DijkstraRouting.DijkstraRouting

        <params to be impliemnted when done>
        """
        AbstractRouterAlgorithm.__init__(self)
        self._k = k
        self._l = l
        self._m = m
        self._bw_per_route_entry = bw_per_route_entry
        self._max_bw = max_bw

    def route(self, routing_info_allocation, placements, machine, subgraph):
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
        :param subgraph: the subgraph object
        :type subgraph: pacman.subgraph.subgraph.Subgraph
        :return: The discovered routes
        :rtype: :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """
        nodes_info = self._initiate_node_info(machine)
        dijkstra_tables = self._initiate_dijkstra_tables(machine)
        self._update_weights(nodes_info, machine)

        #each subsertex represents a core in the board
        progress = ProgressBar(len(placements.placements),
                               "on creating routing entries for each subvertex")
        for placement in placements:
            subvert = placement.subvertex
            out_going_sub_edges = \
                subgraph.outgoing_subedges_from_subvertex(subvert)

            dest_processors = []
            subedges_to_route = list()
            xs, ys, ps = placement.x, placement.y, placement.p

            for subedge in out_going_sub_edges:
                dest_processors.append(machine.get_chip_at(placement.x,
                                                           placement.y)
                                       .get_processor_with_id(placement.p))
                subedges_to_route.append(subedge)

            if len(dest_processors) != 0:
                self._update_weights(nodes_info, machine)
                self._reset_tables(dijkstra_tables)
                xa, ya = xs, ys
                dijkstra_tables["{}:{}".format(xa, ya)]["activated?"] = True
                dijkstra_tables["{}:{}".format(xa, ya)]["lowest cost"] = 0
                self._properate_costs_till_reached_destinations(
                    dijkstra_tables, nodes_info, xa, ya, dest_processors, xs,
                    ys)

            for subedge in subedges_to_route:
                subedge_routing_info = \
                    routing_info_allocation.\
                    get_subedge_information_from_subedge(subedge)
                dest = subedge.post_subvertex
                xd, yd, pd = dest.placement.processor.get_coordinates()
                self._retrace_back_to_source(
                    xd, yd, machine, nodes_info, dijkstra_tables,
                    subedge_routing_info, pd)
            progress.update()
        progress.end()
        return self._routing_tables

    def _initiate_node_info(self, machine):
        """private method DO NOT CALL FROM OUTSIDE BASIC DIJKSTRA ROUTING. \
        used for setting up a dictonary which contaisn data for each chip in \
        the machine

        :param machine: the machine object
        :type machine: spinnmachine.machine.Machine
        :return nodes_info dictonry
        :rtype: dict
        :raise None: this method does not raise any known exceptions
        """
        nodes_info = dict()
        for chip in machine.chips:
            x, y = chip.x, chip.y
            # get_neighbours should return a list of
            # dictionaries of 'x' and 'y' values
            nodes_info["{}:{}".format(x, y)] = dict()
            nodes_info["{}:{}".format(x, y)]["neighbours"] = \
                machine.get_chip(x, y).router.get_neighbouring_chips_coords()

            nodes_info["{}:{}".format(x, y)]["bws"] = []

            nodes_info["{}:{}".format(x, y)]["weights"] = []

            for i in range(len(nodes_info["{}:{}".format(x, y)]["neighbours"])):

                nodes_info["{}:{}".format(x, y)]["weights"].append(None)

                if nodes_info["{}:{}".format(x, y)]["neighbours"][i] is None:

                    nodes_info["{}:{}".format(x, y)]["bws"].append(None)

                else:

                    nodes_info["{}:{}".format(x, y)]["bws"].append(self._max_bw)
        return nodes_info

    def _initiate_dijkstra_tables(self, machine):