class Router:
    """ Used to find routes through a machine
    """

    def __init__(self, router_algorithm=None):
        """
        :param router_algorithm: The router algorithm.  If not specified, a\
                    default algorithm will be used
        :type router_algorithm:\
                    :py:class:`pacman.operations.router_algorithms.abstract_router_algorithm.AbstractRouterAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    router_algorithm is not valid
        """
        pass

    def run(self, routing_info_allocation, placements, machine):
        """ Execute the router algorithm, finding the routes through the\
            machine for the given placed subedges
            
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