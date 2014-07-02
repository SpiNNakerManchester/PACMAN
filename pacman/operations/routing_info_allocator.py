class RoutingInfoAllocator:
    """ Used to prune the subgraph, removing unused edges
    """

    def __init__(self, routing_info_allocator_algorithm=None):
        """
        :param routing_info_allocator_algorithm: The routing info allocator\
                    algorithm.  If not specified, a default algorithm will be\
                    used
        :type routing_info_allocator_algorithm:\
                    :py:class:`pacman.operations.routing_info_allocator_algorithms.abstract_routing_info_allocator_algorithm.AbstractRoutingInfoAllocatorAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    routing_info_allocator_algorithm is not valid
        """
        pass

    def run(self, subgraph, placements):
        """ Execute the algorithm on the subgraph
        
        :param subgraph: The subgraph to allocate the routing info for
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param placements: The placements of the subvertices
        :type placements: :py:class:`pacman.model.placements.placements.Placements`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """
        pass
