from pacman.operations.router_algorithms.abstract_router_algorithm \
    import AbstractRouterAlgorithm


class DijkstraRouting(AbstractRouterAlgorithm):
    """ An routing algorithm that can find routes for subedges between\
        subvertices in a subgraph that have been placed on a machine by the use
        of a dijkstra shortest path algorithm
    """

    def __init__(self):
        """constructor for the
        pacman.operations.router_algorithms.DijkstraRouting.DijkstraRouting

        <params to be impliemnted when done>
        """
        pass

    def route(self, routing_info_allocation, placements, machine):
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
        :return: The discovered routes
        :rtype: :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """
        pass