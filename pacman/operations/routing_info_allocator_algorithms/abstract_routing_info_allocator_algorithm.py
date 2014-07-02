from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

@add_metaclass(ABCMeta)
class AbstractRoutingInfoAllocatorAlgorithm(object):
    """ An abstract algorithm that can produce routing keys and masks for\
        subedges in a subgraph
    """
    
    @abstractmethod
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
