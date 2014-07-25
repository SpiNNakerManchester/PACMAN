from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm


class BasicRoutingInfoAllocator(AbstractRoutingInfoAllocatorAlgorithm):
    """ An basic algorithm that can produce routing keys and masks for\
        subedges in a subgraph based on the x,y,p of their placement
    """

    def __init__(self):
        """constructor that build a
        pacman.operations.routing_info_allocator_algorithms.BasicRoutingInfoAllocator

        <params to be filled in when implimented>

        """
        pass

    def allocate_routing_info(self, subgraph, placements):
        """ Allocates routing information to the subedges in a subgraph

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